# Assignment: Inspecting the Atlassian MCP Remote Server

This assignment walks you through connecting to the Atlassian MCP Remote Server using **MCP Inspector** and running tools like `create_jira_issue` directly — without writing any agent code.

---

## What is the Atlassian MCP Remote Server?

Atlassian exposes a remote MCP (Model Context Protocol) server at:

```
https://mcp.atlassian.com/v1/mcp
```

This server provides tools that let AI agents read and write Jira issues, Confluence pages, comments, worklogs, and more. Authentication uses HTTP Basic Auth with your Atlassian email and an API key.

In the `2.jira_management` project, the CrewAI agents connect to this server like this:

```python
server_params = {
    "url": "https://mcp.atlassian.com/v1/mcp",
    "transport": "streamable-http",
    "headers": {"Authorization": f"Basic {atlassian_token}"},
}
all_tools = MCPServerAdapter(server_params).tools
```

Before building agents that use this server, it is worth inspecting the server directly to understand what tools are available and how they behave.

---

## Prerequisites

- An Atlassian account with a Jira project you can write to
- An Atlassian API key — generate one at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- Node.js installed (`node -v` to confirm)

---

## Why a Proxy is Required

MCP Inspector runs in your browser. When the browser tries to connect directly to `https://mcp.atlassian.com/v1/mcp`, the request is blocked by **CORS** (Cross-Origin Resource Sharing) — the remote server does not allow direct browser-to-server connections from a `localhost` origin.

MCP Inspector solves this by shipping a built-in **proxy server**. The architecture looks like this:

```
Browser UI (port 6274)
       │
       ▼
Local Proxy Server (port 6277)   ← Node.js, no CORS restrictions
       │
       ▼
https://mcp.atlassian.com/v1/mcp
```

The browser only ever talks to `localhost:6277`. The proxy makes the outbound HTTP request to Atlassian on your behalf, so CORS never applies.

---

## Step 1 — Install MCP Inspector

MCP Inspector is a browser-based UI for connecting to any MCP server and invoking its tools interactively.

```bash
npx @modelcontextprotocol/inspector
```

This starts **two** local servers:

| Server | Default port | Purpose |
|---|---|---|
| Web UI | `6274` | Browser interface |
| Proxy | `6277` | Forwards requests to the remote MCP server |

Open `http://localhost:6274` in your browser.

---

## Step 2 — Connect to the Atlassian MCP Server via the Proxy

In the Inspector UI, look for the **Proxy Server** field (above the transport/URL fields) and confirm it points to:

```
http://localhost:6277
```

This is set automatically — leave it as-is. Then configure the target server:

1. Set **Transport** to `Streamable HTTP`
2. Set **URL** to `https://mcp.atlassian.com/v1/mcp`
3. Open the **Headers** section and add:

| Key | Value |
|---|---|
| `Authorization` | `Basic <base64(email:api_key)>` |

To generate the Base64 token:

```bash
echo -n "you@example.com:YOUR_API_KEY" | base64
```

Paste the output as the value for the `Authorization` header.

4. Click **Connect**

> **Troubleshooting:** If the connection fails with a network error, confirm the proxy is running by visiting `http://localhost:6277` in your browser. If the proxy port changed, update the **Proxy Server** field in the UI to match.

---

## Step 3 — Explore Available Tools

Once connected, click the **Tools** tab in the Inspector. You will see the full list of tools the Atlassian MCP server exposes, including:

- `create_jira_issue`
- `edit_jira_issue`
- `get_jira_issue`
- `search_jira_issues_using_jql`
- `transition_jira_issue`
- `get_confluence_page`
- `create_confluence_page`
- `update_confluence_page`
- and many more

Each tool shows its input schema — the required and optional fields you can pass.

---

## Step 4 — Run the `create_jira_issue` Tool

Select `create_jira_issue` from the tools list. The Inspector will render a form based on the tool's input schema.

Fill in the following fields:

| Field | Example value |
|---|---|
| `cloudId` | `https://your-org.atlassian.net` |
| `projectKey` | `TIME` |
| `summary` | `Test issue created via MCP Inspector` |
| `issueType` | `Task` |

Click **Run Tool**. The response panel will show the newly created issue's key (e.g. `TIME-42`), URL, and full JSON payload.

You can verify the issue was created by visiting your Jira project in the browser.

---

## Step 5 — Try Other Tools

Now that you have a live issue key, experiment with other tools:

**Get an issue:**
- Tool: `get_jira_issue`
- Input: `{ "cloudId": "https://your-org.atlassian.net", "issueKey": "TIME-42" }`

**Add a comment:**
- Tool: `add_comment_to_jira_issue`
- Input: `{ "cloudId": "...", "issueKey": "TIME-42", "comment": "Inspected via MCP Inspector" }`

**Transition the issue:**
- Tool: `get_transitions_for_jira_issue` first to see available transitions
- Then use `transition_jira_issue` with the transition ID

---

## What This Teaches You

| Concept | What you observed |
|---|---|
| MCP over HTTP | The server uses Streamable HTTP transport, not stdio |
| CORS restriction | Browsers cannot call remote MCP servers directly — a server-side proxy is required |
| Inspector proxy | MCP Inspector's built-in proxy at port 6277 bypasses CORS by making the request from Node.js |
| Auth pattern | HTTP Basic Auth with Base64-encoded `email:api_key` |
| Tool schema | Each tool has a typed input schema — the same schema CrewAI uses to call tools |
| Live testing | You can validate API access and tool behavior before writing any agent code |

---

## Connection to the `2.jira_management` Project

The `MCPServerAdapter` in `crew.py` connects to this same server at runtime. Each agent is handed a filtered subset of tools:

```python
all_tools = MCPServerAdapter(server_params).tools
confluence_reader = Agent(
    tools=_filter_tools(all_tools, {"get_confluence_page", "search_confluence_using_cql", ...}),
    ...
)
```

MCP Inspector lets you verify that the tools your agents depend on actually work with your credentials and cloud ID before you run an expensive multi-agent crew.
