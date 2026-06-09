# Project 3 — Release Risk Assessment & Go/No-Go Agent: Reference Architecture

---

## 1. Overview

### Problem Being Solved

Before every software release, engineering and release management teams spend 1–3 hours in a manual pre-release review: walking through open tickets, checking if blockers are resolved, verifying test coverage, and assessing team readiness. This process is inconsistent, depends on tribal knowledge, and the outcome is a gut-feel decision made under time pressure. Bad releases slip through; good releases are delayed unnecessarily.

### Business Value

- Eliminates 1–3 hours of manual pre-release review per release cycle
- Produces a consistent, auditable, data-driven Go/No-Go decision every time
- Surfaces hidden dependency blockers that manual review routinely misses
- Reduces "bad release" incidents by catching unresolved upstream blockers before they reach production
- Creates a historical record of risk scores and decisions that can be used to calibrate the process over time

### The One-Line Question the Agent Answers

> **Given a Jira release version, should we ship it — and if not, exactly what needs to be fixed first?**

---

## 2. Agent Map

| Agent Name | Single Responsibility | Tools It Uses |
|---|---|---|
| **Orchestrator Agent** | Accepts the release version as input, sequences the pipeline, fans out to sub-agents in the correct order, aggregates results, and handles timeouts and partial failures | `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql`, internal state store |
| **Ticket Analyst Agent** | Fetches all Jira tickets for the target `fixVersion`, classifies each by type (bug, story, task, sub-task) and resolution status (open, in-progress, done, won't-do), retrieves sprint capacity via JQL proxy, and emits a structured ticket summary | `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` (with JQL `fixVersion = "v2.4.1"` and with JQL `project = X AND sprint in openSprints()` as a team load proxy), `mcp__claude_ai_Atlassian_Rovo__getJiraIssue`, LLM reasoning |
| **Dependency Graph Agent** | Traverses the dependency graph (blocked-by, depends-on, epic hierarchy, subtask relationships) using BFS with visited-set deduplication and a configurable depth limit; identifies unresolved upstream blockers; detects circular dependencies | `mcp__claude_ai_Atlassian_Rovo__getJiraIssueRemoteIssueLinks`, `mcp__claude_ai_Atlassian_Rovo__getJiraIssue`, BFS traversal loop |
| **CI/CD Enrichment Agent** | Queries CI/CD pipelines for the target version's test pass rate, code coverage delta, and flaky test count; marks data as unavailable if the adapter is unreachable | CI/CD REST API (`GET /builds`, `GET /coverage`), internal timeout guard |
| **Risk Scoring Agent** | Receives structured data from Ticket Analyst, Dependency Graph Agent, and CI/CD Enrichment Agent; computes a weighted risk score across four dimensions; produces a `GoNoGoReport` JSON object with per-dimension scores and a confidence level; uses `temperature=0` for all LLM calls | LLM reasoning (temperature=0), `GoNoGoReport` schema validator, retry loop |
| **Delivery Agent** | Publishes the final risk report to Confluence, posts a summary to Slack, and adds a comment to the release's **tracking issue** in Jira (a dedicated release epic or placeholder ticket whose key is resolved from the version string — see Section 5 Stage 4) | `mcp__claude_ai_Atlassian_Rovo__createConfluencePage` / `mcp__claude_ai_Atlassian_Rovo__updateConfluencePage`, `POST https://hooks.slack.com/services/{WEBHOOK_PATH}` (REST webhook), `mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue` |

### Team Capacity Data Source (Proxy Metric)

The Ticket Analyst Agent approximates team load by calling `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` with the JQL query `project = X AND sprint in openSprints() AND assignee in membersOf("{team_name}")` to retrieve open sprint issues assigned to the relevant release team. The `{team_name}` parameter is provided by the Release Manager at invocation time (alongside the `fixVersion`). The count and status distribution of those issues serves as a proxy for team capacity. This is explicitly a proxy metric: the Jira MCP server does not expose a direct team capacity or sprint velocity endpoint, so open sprint load is used as the best available signal. **Note:** Without scoping by team name, the query returns all teams in the project, inflating the load signal for multi-team projects.

### GoNoGoReport JSON Schema

The Risk Scoring Agent is required to produce a `GoNoGoReport` object conforming to the following schema:

```json
{
  "release_version": "string",
  "recommendation": "GO | NO_GO | CONDITIONAL_GO",
  "composite_score": "integer (0-100)",
  "threshold_used": "integer (0-100)",
  "confidence": "HIGH | MEDIUM | LOW",
  "dimension_scores": {
    "blocker_count": "integer (0-10)",
    "test_health": "integer (0-10)",
    "team_load": "integer (0-10)",
    "dependency_depth": "integer (0-10)"
  },
  "action_items": ["string"],
  "data_completeness": "FULL | PARTIAL",
  "generated_at": "ISO 8601 timestamp"
}
```

> **Note on `threshold_used`:** The Go/No-Go threshold is configurable by the Release Manager before each run (default: 40). The `threshold_used` field records which threshold produced the recommendation, ensuring audit reproducibility — two runs with identical risk scores but different thresholds will produce different recommendations, and both are captured in the record.

This schema is validated by the inline JSON Schema validator after each LLM call in the Risk Scoring Agent. Schema validation failure triggers the structured output retry loop (see Section 7, item 2).

---

## 3. Tools & Integrations

All Jira and Confluence tools are accessed via the `mcp__claude_ai_Atlassian_Rovo__*` MCP server.

| Tool/System | Purpose | Notes |
|---|---|---|
| **Jira MCP — `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql`** | Fetches all issues tagged with the target `fixVersion` using JQL `fixVersion = "v2.4.1"` (with `maxResults=50` and `startAt` pagination); also used with `project = X AND sprint in openSprints()` to approximate team load | Returns issue keys, summaries, types, statuses, and assignees; paginated for releases with 500+ tickets |
| **Jira MCP — `mcp__claude_ai_Atlassian_Rovo__getJiraIssue`** | Fetches full issue detail including fields, labels, priority, and linked issues | Called iteratively during dependency graph BFS traversal; one issue per call (no bulk fetch available) |
| **Jira MCP — `mcp__claude_ai_Atlassian_Rovo__getJiraIssueRemoteIssueLinks`** | Fetches all linked issue relationships for a given issue key (blocked-by, depends-on, clones, is-subtask-of) | Core tool for dependency graph traversal; may be called many times on large releases |
| **Jira MCP — `mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue`** | Posts the Go/No-Go recommendation as a comment on the release version's Jira issue | Scoped to write-comment only; does not mutate issue fields |
| **LLM (Claude Sonnet)** | Classifies tickets, reasons over dependency chains, generates natural-language risk summaries, produces structured JSON output | Called by Ticket Analyst, Dependency Graph Agent, and Risk Scoring Agent; all Risk Scoring Agent calls use `temperature=0` |
| **Structured Output Schema Validator** | Validates that the Risk Scoring Agent's output conforms to the `GoNoGoReport` JSON schema before delivery | Runs inline after each LLM call in the Risk Scoring Agent; triggers retry loop on validation failure |
| **CI/CD REST API — `GET /builds?version={v}`** | Fetches build status, test pass rate, and flaky test count for the target release branch | Optional enrichment layer; system continues with degraded report if unavailable |
| **CI/CD REST API — `GET /coverage?version={v}`** | Fetches code coverage delta (coverage change vs. previous release) | Optional; absence is noted in the report with a caveat |
| **Confluence — `mcp__claude_ai_Atlassian_Rovo__createConfluencePage` / `mcp__claude_ai_Atlassian_Rovo__updateConfluencePage`** | Publishes the full structured risk report to a pre-configured Confluence space under a Release Risk Reports section | Page title includes version string and timestamp for discoverability |
| **Slack — `POST https://hooks.slack.com/services/{WEBHOOK_PATH}`** | Posts a concise Go/No-Go summary (risk score, recommendation, top 3 blockers) to a designated release channel via REST webhook | Uses Slack Block Kit for structured formatting; includes a deep-link to the Confluence report. This is a direct REST webhook call, not an MCP tool — no Slack MCP server is used |
| **Internal State Store (in-memory or Redis)** | Holds the aggregated outputs from each agent across pipeline stages; enables the Orchestrator to detect partial completion on timeout | Keyed by `releaseVersion + runId`; TTL set to 30 minutes |

---

## 4. Orchestration Pattern

### Pattern Name: Hierarchical with Parallel Fan-Out

### Rationale

The release risk assessment has a natural dependency ordering: you cannot score risk before you know what tickets exist, but once you have the ticket list you can analyze dependencies and query CI/CD at the same time since those two concerns are independent. This makes a flat sequential pipeline wasteful. Hierarchical orchestration with a controlled parallel fan-out at the middle stage reduces total wall-clock time while preserving the correctness of data dependencies.

The Orchestrator acts as a stateful coordinator — it does not perform analysis itself, it manages execution order, monitors sub-agent completions, handles partial failures, and enforces the 5-minute hard SLA.

### Specific Stages

**Stage 1 — Ticket Analysis (sequential, blocking)**
The Orchestrator invokes the Ticket Analyst Agent first. No downstream work can begin without the full ticket inventory. The Ticket Analyst returns a structured `TicketSummary` object containing total ticket counts by type and status, a list of open/unresolved tickets, and a boolean `has_potential_blockers` flag. If `has_potential_blockers` is false, the Orchestrator short-circuits to Stage 3 directly, skipping dependency traversal.

**Stage 2 — Parallel Fan-Out (conditional, concurrent)**
If blockers were detected, the Orchestrator fans out to two agents simultaneously:
- **Dependency Graph Agent**: traverses issue links using BFS to build the full blocker chain
- **CI/CD Enrichment Agent**: queries build pipelines for test and coverage data

Both run concurrently. The Orchestrator waits for both to complete or until the per-stage timeout (105 seconds, including 15 seconds of coordination overhead) is reached. If either times out, the Orchestrator marks that dimension's data as `UNAVAILABLE` and continues.

**Stage 3 — Risk Scoring (sequential, blocking)**
The Risk Scoring Agent receives the aggregated outputs from Stages 1 and 2. It scores risk across four weighted dimensions and produces a `GoNoGoReport` JSON object. If structured output validation fails, a self-correction retry loop fires (up to 3 retries, with a budget of up to 36 seconds for retries plus 9 seconds overhead).

**Stage 4 — Delivery (sequential, fire-and-forget per channel)**
The Delivery Agent receives the validated `GoNoGoReport` and publishes it to Confluence, Slack, and Jira in parallel sub-calls. Failure of any single delivery channel is logged but does not block the others.

---

## 5. Data & Control Flow

**Trigger:** A Release Manager (or an automated pipeline hook) submits a release version string (e.g., `v2.4.1`) to the Orchestrator Agent, either via a CLI invocation, a Slack slash command, or an automated pre-release pipeline trigger.

**Stage 1 — Ticket Collection and Classification:**
The Orchestrator calls the Ticket Analyst Agent with the version string. The Ticket Analyst calls `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` with JQL `fixVersion = "v2.4.1"` using `maxResults=50` and paginating via the `startAt` offset to retrieve all tickets across multiple pages. For each issue, it uses LLM reasoning to classify the type (bug, feature, task, technical debt) and normalizes the resolution status into one of four buckets: `DONE`, `IN_PROGRESS`, `OPEN`, or `BLOCKED`. The agent also calls `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` with JQL `project = X AND sprint in openSprints()` to retrieve the current sprint's open issues as a proxy for team capacity. All user identity fields are stripped at this data normalization step (see Security NFR). The agent aggregates these into a `TicketSummary` struct and sets `has_potential_blockers = true` if any open issues have status `BLOCKED` or have linked issues of type `is-blocked-by`. The `TicketSummary` is written to the state store and returned to the Orchestrator.

**Conditional Short-Circuit:**
The Orchestrator checks `has_potential_blockers`. If false, it skips Stage 2 entirely — both the Dependency Graph Agent AND the CI/CD Enrichment Agent are skipped. The Orchestrator passes `DependencyReport{status: NOT_APPLICABLE}` and `CICDReport{status: NOT_APPLICABLE}` directly to the Risk Scoring Agent, which treats these dimensions as N/A and redistributes their weights across the remaining dimensions. This short-circuit path reduces total run time from potentially 3–4 minutes to under 90 seconds for clean releases, and avoids hundreds of unnecessary Jira API calls.

**Stage 2 — Parallel Fan-Out (when blockers exist):**
The Orchestrator simultaneously dispatches two sub-agents.

The Dependency Graph Agent uses breadth-first traversal (BFS) starting from each blocked issue, visiting each linked issue once using a visited-set for deduplication, with a configurable depth limit of 5 hops (environment variable `MAX_TRAVERSAL_DEPTH`, default: 5). Circular references are handled by the visited set — if an issue key is already in the visited set, it is not re-enqueued. The agent calls `mcp__claude_ai_Atlassian_Rovo__getJiraIssueRemoteIssueLinks` to retrieve all linked issues for each node in the BFS queue, then calls `mcp__claude_ai_Atlassian_Rovo__getJiraIssue` on any unresolved upstream dependency it encounters. Because there is no bulk issue-fetch MCP tool, each `getJiraIssue` call fetches one issue, so the BFS traversal makes up to `depth_limit × branching_factor` sequential calls — bounded by the depth-5 limit and visited-set deduplication. The output is a `DependencyReport` containing the full blocker chain, depth of the deepest dependency, and a list of unresolved root blockers.

The CI/CD Enrichment Agent calls `GET /builds?version=v2.4.1` and `GET /coverage?version=v2.4.1` against the configured CI/CD adapter. If the adapter is unreachable or returns a non-2xx response within 30 seconds, the agent returns a `CICDReport` with `status: UNAVAILABLE` and all metric fields set to null. This partial report is explicitly noted in the final output.

**Stage 3 — Risk Scoring:**
The Orchestrator collects the `TicketSummary`, `DependencyReport`, and `CICDReport` from the state store once both Stage 2 agents have completed (or timed out). It passes all three to the Risk Scoring Agent.

The Risk Scoring Agent invokes the LLM at `temperature=0` with a structured prompt containing all three data objects and a scoring rubric embedded in the system prompt specifying exact score ranges (e.g., "if unresolved_blocker_count == 0: blocker score = 0; if 1–2: score = 4; if 3+: score = 8–10"). The LLM is instructed to score four dimensions: (1) Blocker Count and Severity, (2) Dependency Chain Depth and Root Blocker Count, (3) CI/CD Health (test pass rate, coverage delta, flaky count), and (4) Team Load (ratio of open/in-progress tickets assigned vs. team capacity proxy). Each dimension is scored 0–10 and multiplied by its configured weight. The weighted sum produces a composite risk score (0–100). The LLM also outputs a confidence level (LOW / MEDIUM / HIGH) based on the completeness of available data, and a Go, No-Go, or Conditional Go recommendation with specific action items for any No-Go condition.

The structured output is validated against the `GoNoGoReport` JSON schema (defined in Section 2). If validation fails, the retry loop fires:
- **Retry 1:** Append the explicit JSON schema definition to the prompt
- **Retry 2:** Reduce temperature to 0 (already set) and add "Output ONLY valid JSON, no prose" to the prompt
- **Retry 3:** Use a simplified prompt with only mandatory fields (`recommendation`, `composite_score`, `action_items`)
- **After 3 failures:** Return `GoNoGoReport{data_completeness: PARTIAL, recommendation: HUMAN_REVIEW_REQUIRED}` with raw scores in an unstructured field

**Stage 4 — Delivery:**
The validated `GoNoGoReport` is passed to the Delivery Agent. It executes three delivery operations:
1. Calls `mcp__claude_ai_Atlassian_Rovo__createConfluencePage` (or `mcp__claude_ai_Atlassian_Rovo__updateConfluencePage` if a page already exists for this version) to publish the full report including per-dimension scores, blocker details, and action items.
2. Calls `POST https://hooks.slack.com/services/{WEBHOOK_PATH}` with a condensed Block Kit summary showing the composite score, the recommendation, confidence level, and a deep-link to the Confluence page.
3. Calls `mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue` on the **release tracking issue** — a dedicated release epic or placeholder ticket, identified by a naming convention: the Orchestrator first calls `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` with JQL `project = ENG AND labels = "release-tracker" AND summary ~ "v2.4.1"` to resolve the issue key; if no match is found, the Delivery Agent skips the Jira comment and logs a warning. This is necessary because Jira `fixVersion` objects are project metadata, not issues — `addCommentToJiraIssue` targets an issue key, not a version name.

The Orchestrator marks the run as `COMPLETE` in the state store and logs the final risk score, recommendation, confidence, `threshold_used`, and full decision path to the decision audit log (a Langfuse trace — see NFR 4).

**Total elapsed time target: under 5 minutes for releases up to 500 tickets.**

---

## 6. Diagrams

### 6.1 System Context Diagram

```mermaid
graph TD
    RM["Release Manager"]
    Pipeline["CI/CD Pipeline Trigger"]

    RRS["Release Risk System"]

    Jira["Jira (Atlassian Rovo MCP)"]
    CICDSys["CI/CD System"]
    Confluence["Confluence"]
    Slack["Slack"]
    LLMProvider["LLM Provider (Claude Sonnet)"]

    RM -->|"submit fixVersion"| RRS
    Pipeline -->|"pre-release hook"| RRS

    RRS -->|"read issues (JQL)"| Jira
    Jira -->|"issue data"| RRS

    RRS -->|"GET /builds, GET /coverage"| CICDSys
    CICDSys -->|"build + coverage metrics"| RRS

    RRS -->|"createConfluencePage / updateConfluencePage"| Confluence
    Confluence -->|"report deep-link"| RM

    RRS -->|"POST webhook"| Slack
    Slack -->|"Go/No-Go summary"| RM

    RRS -->|"prompt + structured data"| LLMProvider
    LLMProvider -->|"GoNoGoReport JSON"| RRS
```

### 6.2 Agent Map Diagram

```mermaid
graph TD
    OA["Orchestrator Agent\n(sequence + fan-out control)"]

    TA["Ticket Analyst Agent"]
    TA_T1["searchJiraIssuesUsingJql\n(fixVersion + openSprints)"]
    TA_T2["getJiraIssue"]
    TA_T3["LLM: classify + summarise"]

    subgraph parallel_stage2["Stage 2 — Parallel Fan-Out (simultaneous)"]
        DGA["Dependency Graph Agent"]
        DGA_T1["getJiraIssueRemoteIssueLinks"]
        DGA_T2["getJiraIssue"]
        DGA_T3["BFS traversal + visited set\n(MAX_TRAVERSAL_DEPTH=5)"]

        CICD_A["CI/CD Enrichment Agent"]
        CICD_T1["GET /builds"]
        CICD_T2["GET /coverage"]
        CICD_T3["timeout guard"]
    end

    RSA["Risk Scoring Agent"]
    RSA_T1["LLM: weighted risk scoring\n(temperature=0)"]
    RSA_T2["GoNoGoReport schema validator"]
    RSA_T3["retry loop (max 3)"]

    DA["Delivery Agent"]
    DA_T1["createConfluencePage /\nupdateConfluencePage"]
    DA_T2["POST Slack webhook"]
    DA_T3["addCommentToJiraIssue"]

    OA -->|"stage 1: ticket list"| TA
    TA --> TA_T1
    TA --> TA_T2
    TA --> TA_T3
    TA -->|"TicketSummary"| OA

    OA -->|"stage 2a: parallel fan-out\n(if blockers detected)"| DGA
    DGA --> DGA_T1
    DGA --> DGA_T2
    DGA --> DGA_T3
    DGA -->|"DependencyReport"| OA

    OA -->|"stage 2b: parallel fan-out\n(simultaneous with DGA)"| CICD_A
    CICD_A --> CICD_T1
    CICD_A --> CICD_T2
    CICD_A --> CICD_T3
    CICD_A -->|"CICDReport"| OA

    OA -->|"stage 3: all data"| RSA
    RSA --> RSA_T1
    RSA --> RSA_T2
    RSA --> RSA_T3
    RSA -->|"GoNoGoReport"| OA

    OA -->|"stage 4: report"| DA
    DA --> DA_T1
    DA --> DA_T2
    DA --> DA_T3
```

### 6.3 Sequence Diagram — Happy Path

```mermaid
sequenceDiagram
    participant RM as Release Manager
    participant OA as Orchestrator Agent
    participant TA as Ticket Analyst Agent
    participant Jira as Jira MCP Server
    participant DGA as Dependency Graph Agent
    participant CICD_A as CI/CD Enrichment Agent
    participant CICDSys as CI/CD System
    participant LLM as LLM Provider
    participant RSA as Risk Scoring Agent
    participant DA as Delivery Agent
    participant Confluence as Confluence
    participant Slack as Slack

    RM->>OA: submit_release_version("v2.4.1")
    OA->>TA: analyze_tickets(fixVersion="v2.4.1")
    TA->>Jira: searchJiraIssuesUsingJql(fixVersion="v2.4.1", maxResults=50, startAt=0)
    Jira-->>TA: [issue list, paginated]
    TA->>Jira: getJiraIssue(key) [for unresolved issues]
    Jira-->>TA: issue detail
    TA->>Jira: searchJiraIssuesUsingJql(project=X AND sprint in openSprints())
    Jira-->>TA: [sprint issues for team load proxy]
    TA-->>OA: TicketSummary{total=47, open=3, blocked=2, has_potential_blockers=true}

    alt no unresolved blockers detected
        OA->>RSA: shortcircuit(TicketSummary, DependencyReport{status: NOT_APPLICABLE}, CICDReport{status: NOT_APPLICABLE})
    else blockers detected
        par Dependency traversal
            OA->>DGA: traverse_dependencies(blocked_issues=[PROJ-101, PROJ-88])
            DGA->>Jira: getJiraIssueRemoteIssueLinks("PROJ-101")
            Jira-->>DGA: links: [is-blocked-by PROJ-55]
            DGA->>Jira: getJiraIssue("PROJ-55")
            Jira-->>DGA: PROJ-55 status=OPEN
            DGA->>Jira: getJiraIssueRemoteIssueLinks("PROJ-55")
            Jira-->>DGA: links: [] (no further blockers)
            DGA-->>OA: DependencyReport{root_blockers=[PROJ-55], max_depth=2, cycles=[]}
        and CI/CD enrichment
            OA->>CICD_A: fetch_cicd_metrics(version="v2.4.1")
            alt CICDSys available
                CICD_A->>CICDSys: GET /builds?version=v2.4.1
                CICDSys-->>CICD_A: {pass_rate: 0.94, coverage_delta: +2.1%, flaky_count: 3}
                CICD_A->>CICDSys: GET /coverage?version=v2.4.1
                CICDSys-->>CICD_A: {coverage_delta: -1.2%}
                CICD_A-->>OA: CICDReport{status: OK, pass_rate: 0.94, coverage_delta: -1.2, flaky_count: 3}
            else CICDSys unavailable (503/timeout)
                CICD_A-->>OA: CICDReport{status: UNAVAILABLE}
                Note over RSA: Redistribute CI/CD weight (20%) proportionally to other dimensions
            end
        end
    end

    OA->>RSA: score_release_risk(TicketSummary, DependencyReport, CICDReport)
    RSA->>LLM: score_dimensions(data, rubric, temperature=0)
    LLM-->>RSA: GoNoGoReport JSON
    RSA->>RSA: validate GoNoGoReport schema

    loop up to 3 retries
        alt schema invalid
            RSA->>LLM: re-score with explicit JSON formatting instructions
            LLM-->>RSA: revised GoNoGoReport JSON
            RSA->>RSA: validate GoNoGoReport schema
        end
    end

    RSA-->>OA: GoNoGoReport{score=68, recommendation=NO_GO, confidence=HIGH, action_items=["Resolve PROJ-55 blocking PROJ-101 before release"]}

    OA->>DA: deliver_report(GoNoGoReport)
    DA->>Confluence: createConfluencePage("Release Risk: v2.4.1", full_report)
    Confluence-->>DA: page_url
    DA->>Slack: POST https://hooks.slack.com/services/{WEBHOOK_PATH} (summary+page_url)
    Slack-->>DA: ok
    DA->>Jira: addCommentToJiraIssue(releaseIssue, formatted_summary)
    Jira-->>DA: ok
    DA-->>OA: delivery_complete{channels=[confluence, slack, jira]}

    OA-->>RM: run_complete{score=68, recommendation=NO_GO, report_url=page_url}
```

---

## 7. Key Agentic Behaviors

1. **Conditional Planning / Short-Circuit (no blockers detected)**
   After the Ticket Analyst completes Stage 1, the Orchestrator evaluates the `has_potential_blockers` flag before committing to Stage 2. If no blocked or dependency-linked open tickets exist, the Orchestrator skips Stage 2 entirely — both the Dependency Graph Agent AND the CI/CD Enrichment Agent are skipped. The Orchestrator passes `DependencyReport{status: NOT_APPLICABLE}` and `CICDReport{status: NOT_APPLICABLE}` directly to the Risk Scoring Agent. When both Dependency (30%) and CI/CD (20%) dimensions are NOT_APPLICABLE, the Risk Scoring Agent redistributes the combined 50% weight proportionally across the two remaining dimensions: Blocker Count receives +21.9% (new weight: 56.9%) and Team Load receives +9.4% (new weight: 24.4%). This is calculated as: Blocker Count gets 35/50 × 50% = 35%; Team Load gets 15/50 × 50% = 15%. The final report labels these dimensions `NOT_APPLICABLE` and notes which weights were applied. This short-circuit path reduces total run time from potentially 3–4 minutes to under 90 seconds for clean releases, and avoids hundreds of unnecessary Jira API calls. This is a genuine planning decision made at runtime based on observed data, not a static workflow branch.

2. **Self-Correction via Structured Output Retry Loop**
   The Risk Scoring Agent is required to emit a `GoNoGoReport` that conforms to the strict JSON schema defined in Section 2. After each LLM call, the output is validated against the schema using a JSON Schema validator. If validation fails (missing field, wrong type, out-of-range score), the retry strategy escalates progressively:
   - **Retry 1:** Append the explicit JSON schema definition to the prompt with the original data and the specific validation errors.
   - **Retry 2:** Reduce temperature to 0 (already set) and add "Output ONLY valid JSON, no prose." to the prompt.
   - **Retry 3:** Use a simplified prompt with only mandatory fields (`recommendation`, `composite_score`, `action_items`).
   - **After 3 failures:** Return `GoNoGoReport{data_completeness: PARTIAL, recommendation: HUMAN_REVIEW_REQUIRED}` with raw dimension scores in a `raw_scores_unvalidated` field so delivery is not blocked.

3. **Graceful Degradation When CI/CD Data Is Unavailable**
   The CI/CD Enrichment Agent enforces a hard 30-second timeout. If the CI/CD adapter is unreachable, returns an error, or times out, the agent returns `CICDReport{status: UNAVAILABLE}` with all metric fields null rather than propagating an exception. The Risk Scoring Agent is designed to handle this: the CI/CD health dimension weight (20%) is redistributed **proportionally** across the remaining three dimensions — Blocker Count receives +8.75% (new weight: 43.75%), Dependency Chain receives +7.5% (new weight: 37.5%), and Team Load receives +3.75% (new weight: 18.75%). These values are computed as: 35/80 × 20%, 30/80 × 20%, and 15/80 × 20% respectively, where 80 is the sum of the remaining weights. The final report includes a prominent `data_completeness: PARTIAL` flag with a note explaining that CI/CD metrics were unavailable at assessment time. The confidence level is capped at MEDIUM when CI/CD data is absent. This ensures a useful (if incomplete) report is always delivered — a silent failure that produces no report is worse than a partial report that flags its own limitations.

4. **How the Risk Scoring Model Works (weighted dimensions)**
   The risk score is not a simple count of open tickets. The Risk Scoring Agent evaluates four independent dimensions, each scored 0–10 by the LLM, then applies configured weights to produce a composite score (0–100). To maximize reproducibility, all Risk Scoring Agent LLM calls use `temperature=0`. A scoring rubric is embedded in the system prompt specifying exact score ranges — for example: "if unresolved_blocker_count == 0: blocker score = 0; if 1–2: score = 4; if 3+: score = 8–10."
   - **Blocker Count and Severity (weight: 35%)** — not just how many blockers exist, but whether any are P0/P1, whether they are on the critical path to the release, and whether they have owners actively working on them.
   - **Dependency Chain Depth and Root Blocker Count (weight: 30%)** — a single unresolved root blocker with a chain depth of 5 is riskier than three independent blockers with no upstream dependencies, because one fix is required vs. three.
   - **CI/CD Health (weight: 20%)** — test pass rate below 95%, coverage delta below -2%, or more than 5 flaky tests each independently elevate this dimension score.
   - **Team Load (weight: 15%)** — ratio of open/in-progress tickets relative to the team's sprint capacity proxy (open sprint issues); high load increases the probability that blockers remain unresolved before release.
   Go is recommended if the composite score is below the configured threshold (default: 40). No-Go is recommended at or above the threshold. The threshold is configurable by the Release Manager at invocation time, and the value used is recorded in the `GoNoGoReport.threshold_used` field for auditability — ensuring that two runs with identical risk scores but different thresholds produce distinct, traceable records.

5. **Confidence Level Output (and Why It Matters for Human Override)**
   The Risk Scoring Agent outputs one of three confidence levels: HIGH, MEDIUM, or LOW. Availability is assessed at the **dimension level**, where each dimension is classified based on the availability of its sub-metrics:
   - **AVAILABLE**: all sub-metrics for the dimension are present
   - **PARTIAL**: at least one sub-metric is present but at least one is absent (e.g., CI/CD dimension is PARTIAL if build pass rate is available but coverage delta is absent)
   - **UNAVAILABLE**: all sub-metrics for the dimension are absent (e.g., CI/CD dimension is UNAVAILABLE if the adapter returned no data)

   The confidence level is then computed using the following decision table:

   | Condition | Confidence |
   |---|---|
   | All 4 dimensions AVAILABLE | HIGH |
   | Exactly 1–2 dimensions PARTIAL (none UNAVAILABLE) | MEDIUM |
   | Any dimension UNAVAILABLE, OR 3+ dimensions PARTIAL | LOW |

   The confidence level is displayed prominently in the Slack and Jira delivery outputs alongside the recommendation. A No-Go with HIGH confidence should require a formal override with a documented reason. A No-Go with LOW confidence is a signal for the Release Manager to manually investigate the data gaps before deciding.

---

## 8. Non-Functional Requirements

### NFR 1: Security — Read-Only Jira Scopes, No PII to External LLM

**Requirement:** The agent must never mutate Jira issue fields, transitions, or assignments. The only write operation permitted against Jira is `addCommentToJiraIssue`. All LLM calls must exclude personally identifiable information (assignee names, email addresses, user IDs).

**Risk:** An agent with write permissions could accidentally or maliciously transition issues, change priorities, or reassign work — causing data integrity problems in the project management system. Sending PII to a third-party LLM provider violates data handling obligations and may expose employee information.

**Design Approach:** The Jira MCP server is configured with a dedicated service account that holds only two permission scopes: `read:jira-work` (for issue reads) and `write:jira-comment` (for the Delivery Agent's `addCommentToJiraIssue` call). All other write scopes are explicitly denied. Before any LLM call, the Ticket Analyst's data normalization step strips all structured user identity fields (assignee email, reporter email, display names) from the issue data, replacing assignee names with anonymous role labels like `Engineer-A`. Additionally, Jira ticket free-text fields (summary, description, comments) are passed through a PII regex scrubber that removes email addresses, phone numbers, and alphanumeric customer IDs matching the pattern `CUST-\d+` before being included in any LLM prompt. The LLM prompt template is static and audited; no user-supplied content is inserted raw into the system prompt.

### NFR 2: Reliability — 5-Minute Hard SLA and Partial Report on Timeout

**Requirement:** The full Go/No-Go report must be available within 5 minutes of the trigger. If the 5-minute deadline is reached before completion, the system must deliver a partial report flagging which stages completed and which did not, rather than silently timing out.

**Risk:** A release is often triggered 15–30 minutes before a scheduled deployment window. If the assessment agent hangs or runs long due to a slow Jira API or large dependency graph, the Release Manager has no information to act on and may either delay the release or proceed blindly.

**Design Approach:** The Orchestrator enforces per-stage time budgets that sum to the 5-minute hard SLA:

| Stage | Budget | Notes |
|---|---|---|
| Stage 1 — Ticket Analysis | 75s | Sequential, blocking |
| Stage 2 — Parallel Fan-Out | 90s | Parallel; includes 15s coordination overhead |
| Stage 3 — Risk Scoring | 75s | Includes retries: max 3 × 20s = 60s + 15s overhead. Assumes p95 Claude Sonnet latency of ~20s for complex structured prompts. |
| Stage 4 — Delivery | 30s | Fire-and-forget per channel |
| Coordination overhead (total) | 30s | Distributed across stages |
| **Total** | **300s = 5 minutes** | |

If any stage timeout is reached, the Orchestrator marks that stage's output as `TIMED_OUT`, increments a partial completion counter, and continues to the next stage with the available data. If the Risk Scoring Agent receives a timed-out dependency report, it scores that dimension as high risk (fail safe: missing blocker data is treated as a risk signal, not a clean signal). The final report always includes a `stages_completed` field so the Release Manager can see exactly what data the recommendation was based on.

### NFR 3: Scale — Releases with 500+ Tickets

**Requirement:** The system must handle releases containing up to 500 Jira tickets without exceeding the 5-minute SLA or exhausting Jira API rate limits.

**Risk:** The Jira MCP server has API rate limits (typically 100–300 requests/minute for REST APIs). A naive implementation that calls `getJiraIssue` for every ticket in the release, then `getJiraIssueRemoteIssueLinks` for every blocker, could easily generate 500–1500 API calls, hitting rate limits and adding minutes to the run time.

**Design Approach:** The Ticket Analyst uses `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` with `maxResults=50` and pagination via the `startAt` offset to retrieve all tickets in the fixVersion across multiple pages. There is no bulk issue-fetch MCP tool; each `mcp__claude_ai_Atlassian_Rovo__getJiraIssue` call fetches one issue. The Dependency Graph Agent's BFS traversal therefore makes up to `depth_limit × branching_factor` sequential `getJiraIssue` calls — bounded by the depth-5 limit (configurable via `MAX_TRAVERSAL_DEPTH`, default: 5) and visited-set deduplication (see Section 5 for the authoritative BFS description). Calls are rate-limited to 80 requests/minute with an exponential backoff retry on 429 responses. For very large releases (>300 tickets), the Ticket Analyst pre-filters to only pass tickets with status `OPEN` or `BLOCKED` to the Dependency Graph Agent, reducing traversal scope.

### NFR 4: Observability — Risk Score Trends and Decision Audit Log

**Requirement:** Every Go/No-Go decision must be logged with the full risk score breakdown, the final recommendation, and the complete decision path. Risk score trends across releases must be queryable to support process improvement.

**Risk:** Without an audit trail, it is impossible to know whether the agent's recommendations have been accurate over time, whether teams are systematically overriding No-Go recommendations and whether those overrides lead to incidents, or which risk dimensions are consistently elevated for a given team or product area.

**Design Approach:** After every run, the Orchestrator captures the complete decision path as a **Langfuse trace** (the observability platform used throughout the cohort). The trace includes a top-level span for the full Orchestrator run, child spans for each agent (Ticket Analyst, DGA, CICD, RSA, Delivery), and LLM generations for all Claude calls. The following fields are recorded as Langfuse trace metadata: `run_id`, `release_version`, `timestamp`, `composite_score`, `threshold_used`, `dimension_scores[4]`, `recommendation`, `confidence`, `stages_completed`, `short_circuit_fired` (boolean), `rsa_retry_attempts` (integer), `unavailable_dimensions` (list), `human_override` (populated if a Release Manager proceeds despite No-Go), `human_override_reason` (free text), and `actual_outcome` (populated post-release).

The `threshold_used` field ensures audit reproducibility: if the same release is scored with two different thresholds, both records show which threshold produced which recommendation.

The audit log captures the full decision path — not just the final recommendation — including: whether the short-circuit fired (skipping DGA and CI/CD), how many RSA retry attempts occurred before a valid schema was produced, which data dimensions were UNAVAILABLE at scoring time, and whether a human override was applied.

The `actual_outcome` field is populated by a post-release webhook: when a PagerDuty incident is created within 72 hours of a GO decision for the same release version, the incident ID and severity are written back to the Langfuse trace as a custom score. For releases without production incidents, `actual_outcome` defaults to `NO_INCIDENT` after 72 hours.

A **Langfuse dashboard** surfaces: risk score trend per team over time, No-Go override rate, correlation between risk score and post-release incident rate, and CI/CD health trends by version — using Langfuse's built-in trace filtering, custom score aggregations, and dataset views.

---

## 9. Edge Cases & Failure Modes

### Edge Case 1: Jira API Timeout During Dependency Traversal

**Scenario:** The Dependency Graph Agent is mid-traversal on a release with a deep dependency chain. The Jira MCP server becomes slow or unresponsive, and individual `getJiraIssueRemoteIssueLinks` calls begin timing out after the 5-second per-call timeout.

**Handling:** The Dependency Graph Agent tracks which issue keys have been fully traversed vs. queued. On a per-call timeout, it retries once with exponential backoff (1s, then 2s). After two failures on the same issue, it marks that branch as `TRAVERSAL_INCOMPLETE` and continues with the rest of the BFS queue. The resulting `DependencyReport` includes a `traversal_warnings` list identifying which subtrees could not be fully explored. The Risk Scoring Agent treats any `TRAVERSAL_INCOMPLETE` subtree as a risk signal (unknown blockers are treated as potential blockers). The final report states explicitly that the dependency analysis is partial and recommends manual inspection of the flagged subtrees.

### Edge Case 2: Circular Dependency Loop in Issue Graph

**Scenario:** Issue A is blocked-by Issue B, Issue B is blocked-by Issue C, and Issue C is blocked-by Issue A — a circular dependency in the Jira issue graph.

**Handling:** The Dependency Graph Agent's BFS visited set handles circular references automatically — when issue A is encountered a second time during traversal, it is already in the visited set and is not re-enqueued, preventing infinite loops. In addition, the agent records `circular_dependency_detected: [A -> B -> C -> A]` in the `DependencyReport`. Circular dependencies are surfaced as a named finding in the final Go/No-Go report with a `HIGH RISK` tag, because they represent an unresolvable blocker condition — the release cannot ship while a circular dependency exists in the issue graph.

### Edge Case 3: CI/CD Adapter Unavailable

**Scenario:** The CI/CD REST API is down, returning 503 errors, or is unreachable from the agent's network due to a firewall or VPN issue.

**Handling:** Addressed under Graceful Degradation in Section 7. The CI/CD Enrichment Agent returns `CICDReport{status: UNAVAILABLE}` after the 30-second timeout. The Risk Scoring Agent redistributes the 20% CI/CD weight **proportionally** across the remaining three dimensions: Blocker Count receives +8.75% (35/80 × 20%), Dependency Chain receives +7.5% (30/80 × 20%), and Team Load receives +3.75% (15/80 × 20%). New effective weights: Blocker Count 43.75%, Dependency Chain 37.5%, Team Load 18.75% — total remains 100%. The final report includes a yellow-flag note: "CI/CD metrics were unavailable at assessment time. Risk score reflects blocker and dependency analysis only. Recommend manual CI/CD review before proceeding." Confidence level is capped at MEDIUM.

### Edge Case 4: LLM Structured Output Schema Validation Repeatedly Failing

**Scenario:** After 3 retry attempts, the Risk Scoring Agent still cannot produce a `GoNoGoReport` that passes schema validation. This might occur if the LLM is producing hallucinated field names, out-of-range scores, or malformed JSON.

**Handling:** After 3 failed retries (following the escalating strategy described in Section 7, item 2), the system enters a safe fallback mode. The Orchestrator logs the failure with all 3 raw LLM outputs for debugging. The Risk Scoring Agent emits a `GoNoGoReport` with `recommendation: HUMAN_REVIEW_REQUIRED`, `confidence: LOW`, `data_completeness: PARTIAL`, and includes the raw dimension score estimates in a `raw_scores_unvalidated` field. The Delivery Agent still publishes this partial report to all channels, with a prominent banner: "Automated risk assessment encountered a scoring error. Raw scores are provided below for reference. Manual Go/No-Go decision required before proceeding." This ensures the Release Manager is never left without information, and the failure is made visible rather than silently swallowed.

### Edge Case 5: Human Overrides the No-Go Recommendation

**Scenario:** The agent recommends No-Go with HIGH confidence, but the Release Manager decides to proceed with the release anyway (for business reasons, or because they have context the agent does not).

**Handling:** The Delivery Agent includes an override mechanism in the Slack and Confluence report: a clearly labeled action button ("Override: Proceed with Release") that, when clicked, requires the Release Manager to enter a free-text override reason. This reason is written back to the release version's Jira issue via `mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue` with a structured tag (`[RELEASE-RISK-OVERRIDE]`) for auditability. The override event is written to the Decision Audit Log with the human's stated reason, the original composite score, and the original recommendation. A Slack notification is sent to the release channel confirming the override and its stated rationale. Post-release, if a production incident is linked to this version (via the PagerDuty webhook described in NFR 4), the audit log provides a complete chain: agent said No-Go, human overrode, incident occurred — enabling retrospective calibration of the risk scoring rubric and thresholds.
