# Project 2 — Deflect-or-Defer: A Cost-Aware Support Swarm

> 40-minute group activity: take a working-but-naive multi-agent customer-support system and refine it for production.

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

You run support for a consumer e-commerce brand doing **40,000+ contacts/day**, spiking 4× on promo weekends. Roughly 70% of inbound is repetitive: *"Where is my order?"*, *"Cancel/change my order,"* *"How do I return this?"*, *"Why was I charged twice?"* Your current chatbot is a flat FAQ tree with low deflection (~25%) and high human-handoff cost. Every escalation costs a paid agent ~$4–7; every LLM call costs tokens; CSAT craters when the bot loops or hallucinates a refund policy.

**The question this agent answers:** *"For this specific customer message, can I resolve it correctly and cheaply right now — and if not, who (which model, or which human) should take it?"* The tension is brutal: at this volume, using a frontier model on every message is financially impossible, but using a cheap model on a billing dispute is a CSAT and chargeback risk.

### b) The Baseline You're Given (deliberately naive)

A **fixed sequential pipeline** where *every* message visits *every* agent in order, and every agent uses the **same single mid-tier LLM**. No routing, no triage, no early-exit, no fallback.

| Agent | Single responsibility | Tool(s) |
|---|---|---|
| **Intake Agent** | Normalize the raw message, extract customer ID | CRM / Order MCP (customer lookup) |
| **Retrieval Agent** | *Always* run a vector search over the help-center KB | Vector DB (help-center articles, policy docs) |
| **Order Agent** | *Always* pull full order + shipment status | Order MCP (status, tracking), Payments API (charge history) |
| **Resolution Agent** | Draft the reply using whatever the prior agents returned | Payments API (issue refund), Order MCP (cancel/modify) |
| **Reply Agent** | Format and send the final message to the customer | — |

```
Customer msg
    │
    ▼
[Intake] ─► [Retrieval] ─► [Order] ─► [Resolution] ─► [Reply] ─► Customer
  (CRM)     (Vector DB)   (Order +    (Payments +
                           Payments)   Order write)

  * same mid-tier LLM at every box
  * no triage / no skip / no human handoff / no fallback
```

> The baseline is functional. Your job is to identify where it falls short and make it production-ready.

### c) Your Task — Refine on 4 Dimensions

**1. Multi-agent pattern**
Every message currently visits every agent in the same fixed order. What's the cost of that uniformity? How would you rethink the topology to handle the range of intent types — and what does that do to complexity and failure modes?

**2. Evaluation**
Deflection rate is easy to measure and easy to game. How would you build an evaluation framework that tells you the system is genuinely resolving contacts — not just deflecting them? What can you test before launch vs. only in production?

**3. LLM strategy**
At 40,000+ contacts/day, LLM cost is a real constraint. How would you decide which model handles what — and how would you keep the system operational if your primary provider degrades mid-promo weekend?

**4. Security**
Customer messages flow directly into agents that can move money and modify orders. What's the adversarial risk, and where are the trust boundaries in this system? What safeguards belong at the model level vs. the tool/API level?

### d) Time Limit

40 minutes to refine, 10 minutes to present.

---

## Presentation Format (10 minutes)

1. **The refined agent map** — what you changed and why
2. **Your eval plan** — your primary metric and a guardrail metric (so deflection can't be gamed)
3. **Your LLM strategy** — how you'd allocate models across the pipeline and stay up during a promo-weekend provider outage
4. **Your top security risk** — and how you'd address it

> **Bonus discussion:** Where do you set the confidence threshold for auto-resolving vs. handing to a human? What is the cost of a false deflection vs. an unnecessary escalation?
