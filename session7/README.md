# Session 7 - Assignments

There are two assignments for this session.

---

## Assignment 1 - A2A Protocol (Self-Study)

Go through the **Agent-to-Agent (A2A) Protocol** module in the recorded course. This covers how separate agentic applications discover and communicate with each other using Google's open A2A standard.

The companion reading for this session is available here: [1.A2A.md](1.A2A.md)

No submission required for this assignment — the goal is to build familiarity with the protocol.

---

## Assignment 2 - Architecture Design

Pick **one** of the three projects below, read its problem statement, and design an architecture for the agentic application it describes.

You are not expected to build it. The deliverable is a **design document** - a written or diagrammatic description of your architecture that you can share with the instructor for review.

### Projects

| # | Project | Link |
|---|---|---|
| 1 | Automated Bug Triage & Intelligent Routing Agent | [problem_statement.md](2.group-activity/project_1/problem_statement.md) |
| 2 | Intelligent Sprint Planning Agent | [problem_statement.md](2.group-activity/project_2/problem_statement.md) |
| 3 | Release Risk Assessment & Go/No-Go Agent | [problem_statement.md](2.group-activity/project_3/problem_statement.md) |

### What to Do

1. **Choose one project.** Read its problem statement carefully.
2. **Design the architecture.** Your design document should cover:
   - **Agents** - name each agent and its single responsibility
   - **Tools** - what external systems each agent calls (Jira MCP server, Slack, vector DB, etc.)
   - **Orchestration pattern** - how agents are connected and sequenced
   - **Key agentic behaviors** - what makes this genuinely agentic vs. a rule-based automation
   - **At least 2 non-functional requirements** - security, scale, reliability, or observability
3. **Share your design document with the instructor and other cohort members** for review and feedback. This can be a diagram, a written doc, or both - whatever communicates your architecture clearly.

> **AI is encouraged.** Use Claude, ChatGPT, or any AI tool to help brainstorm and refine your design. Be ready to explain and defend every decision it helps you make.

### Submission

Send your design document to the instructor and other cohort members over WhatsApp. There is no prescribed format - a Miro board, a Google Doc, a markdown file, or a hand-drawn diagram all work equally well as long as the architecture is clearly communicated.
