# Session 8 — Group Activity: Refine a Multi-Agent System for Production

This session is a hands-on group activity. Unlike Session 7 (where you designed an architecture from scratch), here each group is **given** a problem statement **plus a working-but-naive baseline multi-agent implementation**. Your job is to **refine it** — to make it production-ready along four dimensions.

> 💡 **AI is encouraged.** Use Claude, ChatGPT, or any AI tool to brainstorm, refine, and challenge your assumptions — but be ready to explain and defend every decision it helps you make.

---

## Format

| Phase | Duration | What happens |
|---|---|---|
| **Refine the system** | 40 minutes | Each group hardens their assigned baseline in a breakout room |
| **Present** | 10 minutes per group | Each group walks the cohort through their refined design |

Two groups (2–3 learners each) work on separate projects in parallel.

## Projects

| Group | Project | Domain | Link |
|---|---|---|---|
| **A** | 🔥 FireDrill: The On-Call Co-Pilot | SRE / incident response | [problem_statement.md](1.group-activity/project_1/problem_statement.md) |
| **B** | Deflect-or-Defer: A Cost-Aware Support Swarm | E-commerce customer support | [problem_statement.md](1.group-activity/project_2/problem_statement.md) |
| *spare* | Ledger Lockdown: An Invoice-to-Payment Approval Swarm | Fintech / AP automation | [problem_statement.md](1.group-activity/project_3/problem_statement.md) |

> Project 3 is a **spare/swap** — use it for a 3rd group, an alternate domain, or a security-heavy challenge.

## What to Do

Read your assigned problem statement and its baseline implementation, then **refine the baseline** along these four dimensions:

1. **Choose the right multi-agent pattern** — the baseline is deliberately naive (usually a fixed serial chain). What pattern fits better — parallel fan-out, supervisor/router, model cascade, reflection/critic, hierarchical? Justify *why*.
2. **Evaluation** — how would you do **offline, inline, and online** evaluation, and **which metric matters most** for this system?
3. **LLM selection** — which **2–3 LLMs** would you shortlist and **how**? How do you keep **cost low** *and* keep the system **available** (fallbacks, caching, secondary providers)?
4. **Security** — what is the biggest attack surface (hint: untrusted input flowing into tool-calling agents), and how do you close it?

Each problem statement gives you specific hooks under each dimension. You don't have to exhaust them — go deep where it matters most for your system.

## Presentation Format (10 minutes per group)

Each group should be ready to present:

1. **The refined agent map** — a simple diagram of each agent and how they connect, and **which pattern you chose and why**
2. **Your eval plan** — the ONE metric that matters most for your system, and how you'd measure it offline → inline → online
3. **Your 2–3 LLMs** — how you keep cost low and the system available
4. **Your top security risk** — and how you close it

There is no prescribed deliverable format — a whiteboard sketch, a slide, a Google Doc, or a markdown file all work, as long as the four points above come through clearly.
