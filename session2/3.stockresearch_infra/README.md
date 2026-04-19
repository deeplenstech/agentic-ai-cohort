# Stock Research — CDK Infrastructure

## Purpose

This folder contains the AWS CDK infrastructure for deploying the [Stock Research agent](../1.stockresearch/) to **Amazon Bedrock AgentCore Runtime**.

It provisions all the cloud resources needed to run the agent as a containerised, serverless endpoint on AWS:

- Builds a Docker image from the `1.stockresearch` source directory and pushes it to **Amazon ECR**
- Creates an **IAM execution role** with the permissions the runtime needs (Bedrock, ECR, CloudWatch, X-Ray)
- Deploys an **Amazon Bedrock AgentCore Runtime** that serves the agent over a public network endpoint

## Architecture

```
1.stockresearch/          ← agent source code
        │
        ▼
  Docker build (via CDK asset)
        │
        ▼
  Amazon ECR repository   ← stores the container image
        │
        ▼
  Bedrock AgentCore Runtime  (stock_research_agent)
        │  IAM execution role with permissions for:
        │    • Bedrock model invocation
        │    • ECR image pull
        │    • CloudWatch Logs & Metrics
        │    • X-Ray tracing
```

## Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials
- [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) installed (`npm install -g aws-cdk`)
- Python ≥ 3.11
- [UV](https://docs.astral.sh/uv/) (used to generate `requirements.txt` before the Docker build)
- Docker running locally (CDK uses it to build the container image)

## Installation

Install Python dependencies:

```bash
uv sync
```

## Configuration

The stack reads `SERPER_API_KEY` directly from the sibling project's `.env` file at `../1.stockresearch/.env`. Make sure that file exists and contains the key before deploying:

```env
SERPER_API_KEY=your_serper_api_key
```

The container is configured to use the following model by default (set in `src/AgentCoreStack.py`):

```
LARGE_MODEL_ID=bedrock/us.anthropic.claude-sonnet-4-6
```

## Deploying

### 1. Bootstrap (first time only)

CDK bootstrap provisions S3 and ECR assets in your AWS account. Run once per account/region:

```bash
cdk bootstrap
```

### 2. Synthesize (optional — preview CloudFormation template)

```bash
cdk synth
```

### 3. Deploy

```bash
uv run cdk deploy
```

CDK will:
1. Run `generateRequirements.sh` to freeze `uv` dependencies into `requirements.txt`
2. Build the Docker image from `../1.stockresearch/`
3. Push it to ECR
4. Create the IAM execution role and attach the required policy
5. Deploy the Bedrock AgentCore Runtime

On success, the following outputs are printed:

| Output | Description |
|--------|-------------|
| `AgentCoreRuntimeArn` | ARN of the deployed AgentCore Runtime (also exported for cross-stack use) |
| `AgentCoreRuntimeId` | Runtime ID |
| `ECRRepositoryUri` | ECR repository ARN where the image is stored |
| `ExecutionRoleArn` | ARN of the IAM execution role |

## Invoking the Deployed Agent

Once deployed, you can invoke the agent directly via the AWS CLI or the Boto3 SDK. The agent accepts a JSON payload with a `prompt` key (see [agentCoreHandler.py](../1.stockresearch/src/stockresearch/agentCoreHandler.py)).

### AWS CLI

Replace `<RUNTIME_ID>` with the `AgentCoreRuntimeId` output from the deploy step:

```bash
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-id <RUNTIME_ID> \
  --payload '{"prompt": "What is the current stock price of Apple?"}' \
  --region us-east-1
```

### Python (Boto3)

```python
import boto3
import json

client = boto3.client("bedrock-agentcore", region_name="us-east-1")

response = client.invoke_agent_runtime(
    agentRuntimeId="<RUNTIME_ID>",
    payload=json.dumps({"prompt": "Compare Google and Microsoft stock performance this month."})
)

print(response["output"])
```

### What to Expect

The agent runs the full CrewAI pipeline inside the container — searching the web, analyzing data, and returning a structured research report as a string. Cold starts (first invocation after a period of inactivity) may take 30–60 seconds.

## Updating the Agent

After changing the agent code in `../1.stockresearch/`, re-deploy with:

```bash
uv run cdk deploy
```

CDK detects the changed Docker asset, rebuilds and pushes a new image, and updates the runtime.

## Tearing Down

To destroy all resources created by this stack (AgentCore Runtime, IAM role, ECR repository):

```bash
uv run cdk destroy
```

You will be prompted to confirm. This is **irreversible** — the ECR repository and all pushed images will be deleted.

> **Note:** The ECR repository may retain images if the CDK asset removal policy is set to `RETAIN`. Check the ECR console and delete the repository manually if needed.

## Stack Details

- **Stack name:** `StockResearchAgentCore`
- **Stack file:** [src/AgentCoreStack.py](src/AgentCoreStack.py)
- **Entry point:** [app.py](app.py)
- **CDK config:** [cdk.json](cdk.json)
- **Agent source:** [../1.stockresearch/](../1.stockresearch/)
- **Network mode:** Public
- **Agent name in Bedrock:** `stock_research_agent`
