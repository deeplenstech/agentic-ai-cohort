# Assignment 1: Inspecting the Atlassian MCP Remote Server

This assignment walks you through connecting to the Atlassian MCP Remote Server using **MCP Inspector** and running tools like `create_jira_issue` directly — without writing any agent code.

---

## What is the Atlassian MCP Remote Server?

Atlassian exposes a remote MCP (Model Context Protocol) server at:

```
https://mcp.atlassian.com/v1/mcp
```

This server provides tools that let AI agents read and write Jira issues, Confluence pages, comments, worklogs, and more. Authentication uses HTTP Basic Auth with your Atlassian email and an API key.

Before building agents that use this server, it is worth inspecting the server directly to understand what tools are available and how they behave.

---

## Prerequisites

- An Atlassian account with a Jira project you can write to
- An Atlassian API key with the correct scope — follow these steps:
  1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
  2. Click **Create API token with Scope**
  3. When prompted to select an app, choose **Rovo MCP** — this grants the scopes required to call the MCP server tools (Jira read/write, Confluence read/write, etc.)
  4. After creating the token, copy the token immediately — it will not be shown again
- Node.js installed (`node -v` to confirm)

---

## Why a Proxy is Required

MCP Inspector runs in your browser. When the browser tries to connect directly to `https://mcp.atlassian.com/v1/mcp`, the request is blocked by **CORS** (Cross-Origin Resource Sharing) — the remote server does not allow direct browser-to-server connections from a `localhost` origin.

MCP Inspector solves this by shipping a built-in **proxy server**. 

---

## Step 1 — Install MCP Inspector

MCP Inspector is a browser-based UI for connecting to any MCP server and invoking its tools interactively.

```bash
npx @modelcontextprotocol/inspector --proxy https://mcp.atlassian.com
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
3. Set **Connection Type** as `Via Proxy`
4. Open the **Headers** section and add:

| Key | Value |
|---|---|
| `Authorization` | `Basic <base64(email:api_token)>` |

To generate the Base64 token:

```bash
echo -n "you@example.com:YOUR_API_TOKEN" | base64
```

Paste the output as the value for the `Authorization` header.

5. Click **Connect**

---

## Step 3 — Explore Available Tools

Once connected, click the **Tools** tab in the Inspector. You will see the full list of tools the Atlassian MCP server exposes, including:

- `createJiraIssue`
- `editJiraIssue`
- `getJiraIssue`
- `searchJiraIssuesUsingJql`
- `transitionJiraIssue`
- `getConfluencePage`
- `createConfluencePage`
- `updateConfluencePage`
- and many more

Each tool shows its input schema — the required and optional fields you can pass.

---

## Step 4 — Run the `createJiraIssue` Tool

Select `createJiraIssue` from the tools list. The Inspector will render a form based on the tool's input schema.

Fill in the following fields:

| Field | Example value |
|---|---|
| `cloudId` | `https://your-org.atlassian.net` |
| `projectKey` | `your jira project key` |
| `summary` | `Test issue created via MCP Inspector` |
| `issueType` | `Task` |

Click **Run Tool**. The response panel will show the newly created issue's key (e.g. `PROJECTKEY-42`), URL, and full JSON payload.

You can verify the issue was created by visiting your Jira project in the browser.

---

## Step 5 — Try Other Tools

Now that you have a live issue key, experiment with other tools:

**Get an issue:**
- Tool: `getJiraIssue`
- Input: `{ "cloudId": "https://your-org.atlassian.net", "issueIdOrKey": "PROJECTKEY-42" }`

---

## What This Teaches You

| Concept | What you observed |
|---|---|
| MCP protocol using HTTP | The server uses Streamable HTTP as transport layer and JSON-RPC as the data layer |
| Tool schema | Each tool has a typed input schema — the same schema CrewAI uses to call tools |
| Live testing | You can validate API access and tool behavior before writing any agent code |

---
