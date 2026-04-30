# Assignment 2: Jira Management Crew

## Purpose

This project automates Jira project management using [crewAI](https://crewai.com). A single **Jira Project Manager** agent reads a requirements input (text or Confluence page URL), then creates a structured epic with child tasks in a specified Jira project via the **Atlassian MCP server**.

For enhancement requests the agent automatically:
- Assesses whether a **design task** is needed (architectural changes, new integrations, significant UX work)
- Always creates a **security review task** before QA

## How It Works

1. A `jira_request` is passed as input describing what to create and in which project
2. The **Jira Project Manager** agent connects to the Atlassian MCP server (`https://mcp.atlassian.com/v1/mcp`) and uses its Jira tools
3. The agent creates an epic and all child tasks with correct dependencies, then returns a structured summary of everything created

## Installation

Ensure you have Python >=3.12 <3.13 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

Install uv if you haven't already:

```bash
pip install uv
```

Install the dependencies:

```bash
uv sync
```

### Configuring Environment Variables

Copy the template and fill in your values:

```bash
cp .env.template .env
```

Configure the following keys in your `.env` file:

**Model** — the Bedrock model used by the Jira Project Manager agent:

```env
LARGE_MODEL_ID=bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0
```

Your AWS credentials must be configured (via `~/.aws/credentials`, IAM role, or environment variables) with permissions to invoke the Bedrock model.

**Atlassian** — used to authenticate with the Atlassian MCP server:

```env
ATLASSIAN_EMAIL=your_atlassian_account_email
ATLASSIAN_API_KEY=your_atlassian_api_token
```

To get your Atlassian API token:
1. Log in at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token with Scope**, give it a name, and copy the token

**Langfuse** — used for tracing and observability:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

To get your Langfuse keys:
1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create or join an organization, then create a project
3. Go to **Project Settings → API Keys** and copy the public and secret keys

**Customizing the request** — modify the `inputs` dict in [src/jiramanagement/main.py](src/jiramanagement/main.py):

```python
inputs = {
    'jira_request': (
        "I have a todo app. Based on the requirements confluence page create one epic in the project with the ID 'TIME' in the cloud ID: 'https://deeplenstech.atlassian.net'. Based on the requirements confluence page, also create tasks with the parent as the newly created epic. Task dependencies should be effectively set after the tasks have been created. Epic requirements confluence page: \n"
        "https://deeplenstech.atlassian.net/wiki/spaces/~557058fd5ab0b1dd344900a0675e1db1567b47/pages/360449/Reminder+feature+in+my+ToDo+app \n"
        "After you are done with the changes, update the confluence page and add a section containing a table of newly created jira issues along with their summary"
    )
}
```

## Running the Project

```bash
uv run python -m src.jiramanagement.main
```

## Observing Traces in Langfuse

Every run produces a full trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agent follows a **ReAct** (Reason + Act) loop, calling Atlassian MCP tools repeatedly until all Jira items are created. Each LLM call is captured via a custom `LLMOtelListener` that hooks into CrewAI's event bus — necessary because CrewAI 0.186+ bypasses litellm and routes calls through provider-native SDKs directly.

In Langfuse you will see:
- A root `jira_management` span for the entire run
- CrewAI agent and task spans (via `CrewAIInstrumentor`)
- Individual LLM call spans with token usage, input messages, and model output
