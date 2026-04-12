# Prompt Engineering

This is a hands-on exploration of the prompting techniques covered in the session. Pick any LLM powered application you like — ChatGPT, Gemini, Claude, or anything else — and try these out at your own pace.


---

## Try the Prompt Examples

Start by experimenting with the prompt examples. Try both the weaker and stronger versions and notice the difference in output quality.

When crafting your own prompts, use the **RACE framework** as a guide:

- **R**ole — tell the model who it should act as (e.g. "You are an expert financial analyst")
- **A**ction — clearly state what you want it to do (e.g. "Summarize the key risks in this earnings report")
- **C**ontext — provide relevant background so the model has what it needs (e.g. "The audience is a non-technical investor")
- **E**xpectation — specify the format or quality of the output (e.g. "Respond in 3 bullet points, each under 20 words")

**Prompt 1 — Email writing**

- **Weaker**: Write an email to my team
- **Stronger**: Act as a project manager. Write a professional and concise email to my software development team. Inform them that the project deadline for the 'Phoenix' initiative has been moved up from October 10th to October 3rd due to a client request. Mention that a mandatory planning meeting is scheduled for tomorrow at 10 AM via Google Meet to re-allocate tasks. The tone should be motivating, not alarming.

**Prompt 2 — Image generation**

- **Weaker**: Make a picture of a dog
- **Stronger**: You are an expert graphic designer. Generate a photorealistic image of a golden retriever puppy. The puppy should be sitting in a sunny, green field filled with wildflowers. The lighting should be warm, late-afternoon sun (golden hour), creating soft shadows. The image should be from a low angle, in the style of professional nature photography, with a shallow depth of field, making the background slightly blurry.

## Explore These Additional Prompting Techniques

The [Prompting Guide](https://www.promptingguide.ai/) is a great reference. Have a read through these three techniques and try them out:

- [Zero-Shot Prompting](https://www.promptingguide.ai/techniques/zeroshot)
- [Few-Shot Prompting](https://www.promptingguide.ai/techniques/fewshot)
- [Chain of Thought Prompting](https://www.promptingguide.ai/techniques/cot)

---

## Call a Model Directly

Beyond chat interfaces, you can invoke a model directly via the AWS CLI using Amazon Bedrock or equivalent model hosting services. This gives you full control over the request — system prompts, message structure, temperature, and output format.

### Set up the AWS CLI

Install and configure the AWS CLI by following the [official AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html). Once installed, run:

```bash
aws configure
```

You'll be prompted for your AWS Access Key ID, Secret Access Key, default region (`us-east-1`), and output format (`json`).

### Scripts

The [`scripts/`](scripts/) folder contains a set of progressively more involved examples, all invoking a model via `aws bedrock-runtime invoke-model`:

- **[2.system-user.sh](scripts/2.system-user.sh)** — A basic call with a system and user message. The prompt ([1.prompts.md](scripts/1.prompts.md)) asks the model to generate a report on the history of Agentic AI. The request body is in [2.request-body.json](scripts/2.request-body.json). Output is saved to [2.invoke-model-output.json](scripts/2.invoke-model-output.json).

- **[3.structured-system-user.sh](scripts/3.structured-system-user.sh)** — Same prompt, but the system message now instructs the model to return a structured JSON response. Request body in [3.structured-request-body.json](scripts/3.structured-request-body.json). Output is saved to [3.structured-invoke-model-output.json](scripts/3.structured-invoke-model-output.json).

- **[4.structured-v2-system-user.sh](scripts/4.structured-v2-system-user.sh)** — Extends script 3 by post-processing the output with a small Python snippet that strips any `<reasoning>...</reasoning>` blocks from the response before saving the final JSON. Output is saved to [4.structured-v2-invoke-model-output.json](scripts/4.structured-v2-invoke-model-output.json).

- **[6.react-loop.sh](scripts/6.react-loop.sh)** — Sends a ReAct-style prompt ([5.react-prompt.md](scripts/5.react-prompt.md)) asking the model to compare stock prices. The script extracts the model's response and prints either the text content or any tool calls it requested — illustrating the first step of the ReAct loop. Output is saved to [6.tmp-model-output.json](scripts/6.tmp-model-output.json). To simulate the next step, you can manually add a tool result to [6.react-input.json](scripts/6.react-input.json) and re-run the script, mimicking what an orchestration framework like CrewAI does automatically.

---