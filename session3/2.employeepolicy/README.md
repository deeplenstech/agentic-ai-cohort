# Assignment 2: Employee Policy Crew

## Purpose

Welcome to the Employee Policy Crew project, powered by [crewAI](https://crewai.com).

This project answers employee questions about company policies by querying an **Amazon Bedrock Knowledge Base** containing the employee handbook. A single HR Manager agent retrieves the relevant policy content and returns a concise, empathetic response.

## How It Works

1. An `employee_query` is passed as input (e.g. "How many sick leaves are allowed in a year?")
2. The **HR Manager** agent uses the `BedrockKBRetrieverTool` to search the employee handbook stored in an Amazon Bedrock Knowledge Base
3. The agent returns a polite, concise answer grounded in the retrieved policy content

## Installation

Ensure you have Python >=3.12 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling.

First, if you haven't already, install uv:

```bash
pip install uv
```

Navigate to your project directory and install the dependencies:

```bash
uv sync
```

### Configuring Environment Variables

Copy the template and fill in your values:

```bash
cp .env.template .env
```

Configure the following keys in your `.env` file:

**Model** — the Bedrock model used by the HR Manager agent:

```env
LARGE_MODEL_ID=bedrock/us.anthropic.claude-sonnet-4-6
```

**Amazon Bedrock Knowledge Base** — the ID of the KB containing the employee handbook:

```env
BEDROCK_KB_ID=your_bedrock_knowledge_base_id
```

Your AWS credentials must be configured in the environment (via `~/.aws/credentials`, IAM role, or environment variables) with permissions to invoke the Bedrock model and query the Knowledge Base.

**Langfuse** — used for tracing and observability:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

To get your Langfuse keys:

1. **Create an account** — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. **Create an organization** — after login, create or join an organization
3. **Create a project** — create a new project (e.g. `employeepolicy`); each project has its own API keys
4. **Get your API keys** — go to **Project Settings → API Keys** and copy the public and secret keys

**Customizing the query** — modify the `inputs` dict in [src/employeepolicy/main.py](src/employeepolicy/main.py):

```python
inputs = {
    'employee_query': "How many sick leaves are allowed in a year."
}
```

## Running the Project

```bash
uv run python -m src.employeepolicy.main
```

## Observing Traces in Langfuse

Once configured, every run produces a full trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agent follows a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM considers the query and what it needs to look up
2. **Act** — the agent calls the `BedrockKBRetrieverTool` to search the handbook
3. **Observe** — the LLM reads the retrieved chunks
4. **Repeat** — until it has enough context to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span.
