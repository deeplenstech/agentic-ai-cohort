# Project 3 — Ledger Lockdown: An Invoice-to-Payment Approval Swarm

> 40-minute group activity: take a working-but-naive multi-agent invoice-approval system and refine it for production.


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

A mid-market company's Accounts Payable team receives ~4,000 vendor invoices/month as PDFs and email attachments — varying layouts, multiple currencies, scanned images, and embedded "remit-to" instructions. Today, AP clerks manually key fields, cross-check each invoice against the matching Purchase Order and Goods Receipt (the 3-way match), watch for duplicate billing and bank-detail-change fraud, and route exceptions. It is slow (avg. 9 days to approve), error-prone, and a known fraud surface (business email compromise, inflated quantities, invoices split under approval thresholds).

**The question this agent answers:** *"For this incoming invoice, should we PAY, HOLD, or ESCALATE — and what is the evidence?"* The system must output a structured decision with line-item match results, exceptions, a risk score, and a **citation trail an auditor can replay**.

### b) The Baseline You're Given (deliberately naive)

A **fixed sequential pipeline** — every invoice flows through all agents in the same order, one at a time, regardless of type or risk — and **one big LLM does every step**.

| Agent | Single responsibility | Tool(s) |
|---|---|---|
| **Extractor Agent** | OCR + parse the invoice into structured fields (vendor, totals, line items, remit-to bank details) | OCR / Document MCP, LLM extraction |
| **Matcher Agent** | Perform the 3-way match against POs and Goods Receipts | ERP API (POs, receipts), SQL MCP |
| **Compliance Agent** | Check tax validity, sanctions/OFAC list, duplicate-invoice detection | Vector DB (historical invoices), sanctions API |
| **Risk Agent** | Score fraud likelihood (bank-detail change, threshold-splitting, anomalous amounts) | Vector DB, rules lookup |
| **Decision Agent** | Synthesize everything into PAY / HOLD / ESCALATE + rationale | LLM, writes to audit log |

```
  Invoice PDF
      │
      ▼
 [Extractor] ─► [Matcher] ─► [Compliance] ─► [Risk] ─► [Decision] ─► Audit Log

  * every invoice takes the full 5-hop path, serially
  * one big LLM does OCR cleanup AND high-stakes fraud reasoning alike
  * no router, no parallelism, no clean-invoice fast-path, no human-in-loop gate
```

> The baseline is functional. Your job is to identify where it falls short and make it production-ready.

### c) Your Task — Refine on 4 Dimensions

**1. Multi-agent pattern**
Every invoice takes the same 5-hop path regardless of type, value, or risk level. Is that the right design? How would you restructure the topology — and what are the tradeoffs of adding complexity to a system that touches real payments?

**2. Evaluation**
AP errors come in two directions: approving invoices you shouldn't, and holding invoices you should pay. How do you measure the system across both failure modes? Which is more expensive, and how does that shape your evaluation priorities?

**3. LLM strategy**
One large model handles both OCR cleanup and high-stakes fraud reasoning. How would you decide where to use what — and how would you validate that choice rather than just assuming a bigger model is always better?

**4. Security**
The invoice PDFs themselves are attacker-controlled documents. What could a malicious vendor embed, and where would that payload land in your pipeline? What other trust boundaries exist in a system that writes to an audit log and queues payments?

### d) Time Limit

40 minutes to refine, 10 minutes to present.

---

## Presentation Format (10 minutes)

1. **The refined agent map** — what you changed and why
2. **Your eval plan** — the metric that matters most, and how you'd measure it
3. **Your LLM strategy** — how you'd allocate models across the pipeline and handle provider unavailability
4. **Your top security risk** — and how you'd defend against it

> **Bonus discussion:** Where do you set the confidence threshold to auto-approve vs. defer to a human? What happens when the LLM is wrong and an AP clerk overrides the decision — how does that feed back?
