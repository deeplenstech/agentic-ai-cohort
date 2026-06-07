# Project 1 — 🔥 FireDrill: The On-Call Co-Pilot

> 40-minute group activity: take a working-but-naive multi-agent incident-response system and refine it for production.

> 💡 **AI is encouraged.** Use Claude, ChatGPT, or any AI tool to brainstorm, challenge your assumptions, or draft your presentation. Treat AI as a team member — but be ready to explain and defend every decision it helps you make.

---

## How It Works

| Phase | Duration | What happens |
|---|---|---|
| **Refine the system** | 40 minutes | Your group hardens the given baseline along the 4 dimensions below |
| **Present** | 10 minutes | Walk the cohort through your refined design and the tradeoffs you made |

You are given a problem statement **and a working-but-naive baseline implementation**. Your job is **not** to redesign from zero — it is to make it **production-ready**.

---

### a) Problem Statement

At 3:17 AM PagerDuty fires: `checkout-api p99 latency > 2s, error rate 8%`. The on-call SRE now has ~15 minutes of SLA budget and four browser tabs to open: the metrics dashboard, the log explorer, the trace waterfall, and the deploy timeline. They context-switch, eyeball graphs, and try to hold a causal story in their head while half-awake. Mean-time-to-RCA is dominated not by *fixing* but by *correlating* — the signal is almost always already in the telemetry; it is just spread across five systems and a tired human has to stitch it together under time pressure.

**The question this agent answers:** *"Given this firing alert, what is the most likely root cause, what evidence supports it, and what is the single safest next action?"* It does **not** auto-remediate — it compresses the correlation work so the human reaches a decision faster, with citations they can trust at 3 AM.

### b) The Baseline You're Given (deliberately naive)

A single **Orchestrator** drives **five specialist agents strictly one at a time**, in a fixed order, blocking on each before starting the next. Each specialist has one responsibility and one tool.

| Agent | Single responsibility | Tool(s) |
|---|---|---|
| **Orchestrator** | Read the PagerDuty payload, call each specialist sequentially, write the summary | PagerDuty MCP (read incident) |
| **LogAgent** | Pull recent error-level logs for the affected service | Observability/Datadog MCP (logs) |
| **MetricAgent** | Pull metric anomalies (latency, error rate, saturation) | Datadog MCP (metrics) |
| **TraceAgent** | Pull the slowest / erroring trace spans | Datadog MCP (APM/traces) |
| **DeployAgent** | List deploys / PRs in the last 60 min for the service | GitHub / deploy MCP |
| **RunbookAgent** | Retrieve the matching runbook | Vector DB over runbooks |

The Orchestrator queries each source one at a time, appends the **raw output** to a growing context, and only the *final* LLM call attempts correlation. Every agent uses the **same large reasoning model**. No reflection, no parallelism, no cross-checking.

```
        PagerDuty alert
              │
              ▼
      ┌──────────────┐
      │ Orchestrator │
      └──────┬───────┘
             │  (one at a time, blocking)
             ▼
   [LogAgent] ─► wait ─► [MetricAgent] ─► wait ─►
   [TraceAgent] ─► wait ─► [DeployAgent] ─► wait ─►
   [RunbookAgent] ─► wait
             │
             ▼
   single big LLM call: "here's everything, guess the cause"
             │
             ▼
        Summary  (slow, unranked, no confidence, no citations)
```

> The baseline is functional. Your job is to identify where it falls short and make it production-ready.

### c) Your Task — Refine on 4 Dimensions

**1. Multi-agent pattern**
Five agents run sequentially on independent data sources. Is sequential the right choice here? What considerations would guide a different topology — and what new problems might that introduce?

**2. Evaluation**
An on-call engineer receives a summary and acts on it at 3 AM. How do you measure whether the system helps or hurts? Design an approach that covers before deployment, during live incidents, and over time.

**3. LLM strategy**
Every agent uses the same large reasoning model. Should they? How would you decide — and how would you ensure the system stays functional if a provider is unavailable exactly when an incident fires?

**4. Security**
The agents have read access to production telemetry, and the input data originates from systems under active attack or adversarial conditions. What could go wrong, and how does your risk surface change if the system ever takes action rather than just observing?

### d) Time Limit

40 minutes to refine, 10 minutes to present.

---

## Presentation Format (10 minutes)

1. **The refined agent map** — what you changed and why
2. **Your eval plan** — the metric that matters most, and how you'd measure it
3. **Your LLM strategy** — how you'd keep cost low and the system available during a provider outage
4. **Your top security risk** — and how you'd close it

> **Bonus discussion:** Where do you draw the line between "agent suggests, human decides" and letting the agent take a reversible action on its own?
