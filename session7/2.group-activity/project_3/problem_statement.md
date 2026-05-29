# Project 3 — Release Risk Assessment & Go/No-Go Agent

> 1-hour group activity: design the architecture of an agentic Jira automation application.

> 💡 **AI is encouraged.** Use Claude, ChatGPT, or any AI tool to help brainstorm, refine your architecture, challenge your assumptions, or draft your presentation. Treat AI as a team member — but be ready to explain and defend every decision it helps you make.

---

## How It Works

| Phase | Duration | What happens |
|---|---|---|
| **Architecture design** | 40 minutes | Each group designs their assigned agentic application in a Zoom breakout room |
| **Presentation prep** | 20 minutes | Groups prepare a whiteboard/diagram to present back to the cohort |

Your goal is not to build it — it is to design it. Think agents, tools, orchestration patterns, data flow, and the non-functional requirements that would make it production-ready.

---

### a) Problem Statement

Before every software release, engineering and release management teams spend 1–3 hours in a manual pre-release review: walking through open tickets, checking if blockers are resolved, verifying test coverage, and assessing team readiness. This process is inconsistent, depends on tribal knowledge, and the outcome is a gut-feel decision made under time pressure. Bad releases slip through; good releases are delayed unnecessarily.

**The question this agent answers:** *Given a Jira release version, should we ship it — and if not, exactly what needs to be fixed first?*

### b) Expectations

Your group should design an agentic application that:

- **Collects** all Jira tickets in a target `fixVersion` via the **Jira MCP server** and classifies each by type and resolution status
- **Traverses** the dependency graph (blocked-by, depends-on, epic hierarchy) by iteratively querying linked issues through the **Jira MCP server** to identify unresolved upstream blockers
- **Queries** CI/CD pipelines for test pass rates, code coverage delta, and flaky test counts (treat this as an optional enrichment layer if it adds too much scope)
- **Scores** release readiness across multiple risk dimensions (blocker count, test health, team load, dependency depth) using a weighted model
- **Generates** a structured Go/No-Go recommendation with per-dimension risk scores, specific action items for any No-Go condition, and a confidence level
- **Delivers** the report to Confluence, Slack, and as a Jira comment on the release version

Your architecture document should cover:
- **Agents** — name each agent and define its single responsibility (Orchestrator, Ticket Analyst, Dependency Graph Agent, Risk Scoring Agent, etc.)
- **Tools** — **Jira MCP server** (search by fixVersion, fetch issue links, post comments), LLM for reasoning, CI/CD adapter (optional enrichment), structured output enforcement
- **Orchestration pattern** — the natural pattern here is hierarchical with parallel fan-out: Ticket Analyst first, then Dependency + CI/CD in parallel, then Risk Scorer, then delivery
- **Key agentic behaviors** — specifically: conditional planning (short-circuit to low-risk if no blockers found), self-correction (retry if structured output schema validation fails), graceful degradation (deliver partial report if CI/CD data is unavailable)
- **At least 2 NFRs** — pick from: security (read-only Jira scopes, no PII to external LLM), scale (releases with 500+ tickets), reliability (5-minute hard SLA, partial report on timeout), observability (risk score trends over time, decision audit log)

**Bonus discussion:** How do you calibrate the risk scoring rubric? Who sets the Go/No-Go threshold — the agent or a human? How do you handle a team that overrides the agent's No-Go recommendation?

### c) Time Limit

| Milestone | Time |
|---|---|
| Agree on agents and their responsibilities | 15 minutes |
| Design the orchestration flow end-to-end | 15 minutes |
| Discuss NFRs and edge cases | 10 minutes |
| Prepare presentation (diagram + key talking points) | 20 minutes |
| **Total** | **60 minutes** |

---

## Presentation Format (10 minutes per group)

Each group should be ready to present:

1. **The agent map** — a simple diagram showing each agent, what it does, and how they connect
2. **The orchestration pattern** — sequential? parallel fan-out? hierarchical? why?
3. **The agentic moment** — what is the one behavior in your design that makes this genuinely agentic rather than just a workflow automation?
4. **One hard NFR tradeoff** — what was the toughest non-functional requirement to design for, and how did you approach it?
