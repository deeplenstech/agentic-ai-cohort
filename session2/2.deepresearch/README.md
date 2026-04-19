# Deep Research Crew

## Purpose

Welcome to the Deep Research project, powered by [crewAI](https://crewai.com).

This project uses a multi-agent AI crew to conduct deep, structured research on any topic. Given a research question, the crew decomposes it into sub-questions, investigates each using live web search and content extraction, writes a comprehensive cited article, and applies a critic-review feedback loop before producing the final output.


## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
uv sync
```
### Customizing

**Set up your `.env` file by copying the template:**

```bash
cp .env.template .env
```

Then configure the following keys in your `.env` file:

**Model setup** — set `LARGE_MODEL_ID` to the model you want to use, and provide the corresponding API key:

```env
# Example: Anthropic
LARGE_MODEL_ID=anthropic/claude-sonnet-4-6
ANTHROPIC_API_KEY=your_anthropic_api_key

# Example: OpenAI
LARGE_MODEL_ID=openai/gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

**Tavily** — used by agents to search the web and extract URL content:

```env
TAVILY_API_KEY=your_tavily_api_key
```

Get a free Tavily key at [tavily.com](https://tavily.com).

**Langfuse** — used for tracing and observability:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

To get your Langfuse keys:

1. ***Create an account*** — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. ***Create an organization*** — after login, you'll be prompted to create or join an organization (this is the top-level workspace, e.g. your team or company name)
3. ***Create a project*** — inside your organization, create a new project (e.g. `deepresearch`); each project has its own set of API keys and trace history
4. ***Get your API keys*** — go to **Project Settings → API Keys** and create a new key pair; copy the public and secret keys into your `.env` file

**User Query** - customizing the user query:
Modify `src/deepresearch/main.py` to set the research topic

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ uv run python -m src.deepresearch.main
```

This command initializes the Deep Research crew, assembles the agents, and executes the research pipeline.

This example, unmodified, will produce a structured research article on the configured query.


## Observing the ReAct Cycle in Langfuse

Once you've configured Langfuse and run the crew, you can observe the agent's full reasoning trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agents follow a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM thinks about what it knows and what it needs
2. **Act** — CrewAI calls a tool (e.g. Tavily web search, URL extractor)
3. **Observe** — LLM reads the tool result
4. **Repeat** — until it has enough information to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span. This makes it easy to understand how the agent arrived at its answer and where time or tokens were spent.

## Understanding Your Crew

The Deep Research crew uses four specialist agents — a **Planner**, **Researcher**, **Writer**, and **Critic** — that collaborate to produce a cited research article with a built-in revision loop.

### Crew Variants

Two orchestration patterns are available, each defined in its own file:

| Pattern | File | Description |
|---------|------|-------------|
| Hierarchical Crew | `crew.py` | A manager agent dynamically delegates each step (planning, research, writing, critique) to the right specialist. The control flow is determined at runtime by the manager LLM. |
| Fixed Flow | `flow.py` | A `DeepResearchFlow` with explicit, hard-coded steps: plan → research (parallel per sub-question) → write → critique → route (approve or revise). Control flow is defined in code, not by an LLM. |

To switch between patterns, update the active call in [src/deepresearch/main.py](src/deepresearch/main.py):

```python
# Hierarchical crew — manager LLM orchestrates all steps
response = crew.kickoff(inputs=inputs).raw

# Fixed flow — explicit pipeline with parallel research and revision loop
response = await DeepResearchFlow().kickoff_async(inputs=inputs)
```

Only one call should be active at a time. Comment out or remove the other.
