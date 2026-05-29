# Project 1 — Automated Bug Triage & Intelligent Routing Agent

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

Engineering teams waste 3–5 hours per week in manual bug triage rituals — reading through incoming bug reports, debating severity, figuring out which team or engineer owns the issue, and chasing duplicates. Critical P0 bugs can sit unassigned for hours due to human fatigue or miscommunication. There is no consistent, repeatable process, and the quality of triage depends entirely on who shows up to the meeting.

**The question this agent answers:** *When a new bug lands in Jira, what is it, how urgent is it, has it been reported before, and who should fix it — all within 2 minutes, automatically?*

### b) Expectations

Your group should design an agentic application that:

- **Ingests** new Jira bug tickets in real-time via the **Jira MCP server** (polling or event trigger)
- **Classifies** each bug by severity (P0–P3), component, and type (regression, performance, UX, security) using LLM reasoning — not keyword rules
- **Deduplicates** against existing open tickets using semantic similarity (vector embeddings), and links or closes duplicates automatically
- **Routes** each bug to the correct team or engineer based on component ownership and current workload
- **Notifies** the right people via Slack, and triggers a PagerDuty alert for P0s

Your architecture document should cover:
- **Agents** — name each agent and define its single responsibility
- **Tools** — what external systems each agent calls via the **Jira MCP server** (search issues, update fields, add comments), plus Slack, vector DB, PagerDuty, etc.
- **Orchestration pattern** — how the agents are chained (sequential pipeline with conditional branching is a natural fit here)
- **Key agentic behaviors** — specifically how this goes beyond a rule-based automation (confidence thresholds, self-correction via feedback loop, memory of past routings)
- **At least 2 NFRs** — pick from: security (scoped API tokens, prompt injection), scale (ticket volume, queue-based ingestion), reliability (P0 SLA, dead-letter queue), or observability (routing accuracy dashboard)

**Bonus discussion:** Where do you set the confidence threshold before routing automatically vs. deferring to a human? What happens when the LLM is wrong and an engineer reassigns the ticket?

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
