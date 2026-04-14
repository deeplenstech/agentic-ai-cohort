# Stockresearch Crew

## Purpose

Welcome to the Stockresearch Crew project, powered by [crewAI](https://crewai.com). 

This project uses a single-agent AI crew to automate stock research. Given a stock ticker or company name, the crew researches the company, analyzes relevant financial and market data, and produces a structured research report. It is intended as a starting point for building AI-powered investment research workflows using crewAI.


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

**Model setup** — set `MODEL_ID` to the model you want to use, and provide the corresponding API key:

```env
# Example: Anthropic
MODEL_ID=anthropic/claude-sonnet-4-6
ANTHROPIC_API_KEY=your_anthropic_api_key

# Example: OpenAI
MODEL_ID=openai/gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

**Serper** — used by the agent to search the web for stock data:

```env
SERPER_API_KEY=your_serper_api_key
```

Get a free Serper key at [serper.dev](https://serper.dev).

**Langfuse** — used for tracing and observability:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

To get your Langfuse keys:

1. ***Create an account*** — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. ***Create an organization*** — after login, you'll be prompted to create or join an organization (this is the top-level workspace, e.g. your team or company name)
3. ***Create a project*** — inside your organization, create a new project (e.g. `stockresearch`); each project has its own set of API keys and trace history
4. ***Get your API keys*** — go to **Project Settings → API Keys** and create a new key pair; copy the public and secret keys into your `.env` file

**User Query** - customizing the user query:
Modify `src/stockresearch/main.py` to add custom inputs for the crew

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ uv run python -m src.stockresearch.main
```

This command initializes the stockResearch Crew, assembling the agent and assigning it tasks as defined.

This example, unmodified, will run the create a structure report on the user query.


## Observing the ReAct Cycle in Langfuse

Once you've configured Langfuse and run the crew, you can observe the agent's full reasoning trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agent follows a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM thinks about what it knows and what it needs
2. **Act** — CrewAI(based on Agent configuration) calls a tool (e.g. Serper web search, date tool)
3. **Observe** — LLM reads the tool result
4. **Repeat** — until it has enough information to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span. This makes it easy to understand how the agent arrived at its answer and where time or tokens were spent.

## Understanding Your Crew

The stockResearch Crew is composed of a single AI agent with a defined role, goal, and tools. The agent is configured directly in `crew.py`. It executes tasks based on the stock specified in your query, researching and analyzing that specific company to produce its output.
