# Project 2 — Intelligent Sprint Planning Agent

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

Engineering teams spend 2–4 hours per sprint in planning meetings, manually reconciling backlog priority, team availability, historical velocity, and ticket complexity to commit to a sprint goal. The process relies heavily on the scrum master's experience, is inconsistently applied across teams, and frequently results in over-commitment (15–25% rollover is common) or under-utilisation. New scrum masters take several sprints to reach planning confidence.

**The question this agent answers:** *Given our backlog, team capacity, and historical velocity, what should be in our next sprint — and why?*

### b) Expectations

Your group should design an agentic application that:

- **Analyses the backlog** — queries all backlog tickets via the **Jira MCP server**, scores them by priority (mapping Jira priority levels P0–P3 to numeric weights, optionally boosted by SLA or customer escalation flags), dependency status (excluding blocked/orphaned tickets while applying a scoring bonus to tickets that unblock other high-priority issues), and staleness (calculated dynamically based on ticket priority: e.g., P0/blocker tickets are considered stale if untouched for >2 days, P1/high for >14 days, P2/medium for >30 days, and P3/low for >90 days)
- **Models team capacity** — reads team member availability (PTO, holidays, part-time flags) and computes net sprint capacity in story points
- **Reviews velocity history** — fetches the last 5–8 completed sprints via the **Jira MCP server** to establish a rolling velocity baseline, and flags anomalous sprints (e.g., one disrupted by a production incident)
- **Estimates unestimated tickets** — uses LLM reasoning over ticket descriptions and acceptance criteria, with few-shot examples from the team's own history, to suggest story point ranges
- **Synthesises a draft sprint plan** — selects tickets up to capacity in priority order, avoids blocked/orphaned tickets, annotates each selection with reasoning, and flags risks (single-engineer dependencies, unestimated items)
- **Delivers for human approval** — writes the draft sprint back to Jira via the **Jira MCP server** (not yet activated) and sends a summary to the team via Slack; the sprint is only activated with explicit human approval

Your architecture document should cover:
- **Agents** — name each agent and define its single responsibility (Orchestrator, Backlog Analyst, Capacity Planner, Velocity Historian, Complexity Estimator, Draft Plan Synthesiser)
- **Tools** — **Jira MCP server** (backlog search, sprint history, sprint write-back), calendar API for availability, LLM for estimation and synthesis
- **Orchestration pattern** — parallel fan-out (Backlog Analyst + Capacity Planner + Velocity Historian run simultaneously), converge into Complexity Estimator, then Synthesiser
- **Key agentic behaviors** — specifically: multi-step reasoning (Complexity Estimator reasons over acceptance criteria, not keywords), memory (Velocity Historian excludes anomalous sprints via a short-term store), self-correction (Synthesiser iterates if first plan exceeds capacity), human-in-the-loop (never activates the sprint without approval)
- **At least 2 NFRs** — pick from: security (write-only for Synthesiser, read-only for all others; private LLM inference for sensitive ticket content), scale (backlogs up to 500 tickets, teams up to 15), reliability (plan available within 5 minutes of trigger, idempotent writes), observability (planning accuracy tracked over time via rollover rate)

**Bonus discussion:** What happens when the team ignores the draft and plans manually? How do you build trust before enabling write-back to Jira? How do you handle a sprint where the velocity baseline is unreliable (new team, major incident)?

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
