from aws_cdk import (
    Stack,
    Fn,
    Duration,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    aws_bedrockagentcore as bedrockagentcore,
    aws_cloudwatch as cloudwatch,
    aws_xray as xray,
    CfnOutput,
)
from constructs import Construct
from pathlib import Path
import os
import subprocess

# Load SERPER_API_KEY from 1.stockresearch/.env if the file exists, else blank.
_env_file = Path(__file__).parent / ".." / ".." / "1.stockresearch" / ".env"
_serper_api_key = ""
try:
    for _line in _env_file.read_text().splitlines():
        if _line.startswith("SERPER_API_KEY="):
            _serper_api_key = _line.split("=", 1)[1].strip().strip('"').strip("'")
            break
except FileNotFoundError:
    pass

class AgentCoreStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get account and region info
        account = Stack.of(self).account
        region = Stack.of(self).region

        # Run local command before building to update requirements.txt
        subprocess.run(["sh", "generateRequirements.sh"], check=True, cwd=".")
        
        # Build and push Docker image from agents directory
        docker_image = ecr_assets.DockerImageAsset(
            self,
            "StockResearchDockerImage",
            directory=os.path.join(os.path.dirname(__file__), "..", "..", "1.stockresearch"),
            asset_name="stockresearch-images"
        )

        # IAM execution role for AgentCore runtime
        execution_role = iam.Role(
            self,
            "StockResearchAgentCoreExecutionRole",
            assumed_by=iam.ServicePrincipal(
                "bedrock-agentcore.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "aws:SourceAccount": account
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account}:*"
                    }
                }
            ),
            description="Execution role for Amazon Bedrock AgentCore runtime",
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:DescribeLogStreams",
                    "logs:CreateLogGroup"
                ],
                resources=[f"arn:aws:logs:{region}:{account}:log-group:/aws/bedrock-agentcore/runtimes/*"],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:DescribeLogGroups"
                ],
                resources=[f"arn:aws:logs:{region}:{account}:log-group:*"],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[f"arn:aws:logs:{region}:{account}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"],
            )
        )
        
        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken"
                ],
                resources=["*"],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                resources=[docker_image.repository.repository_arn],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                resources=["*"],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "bedrock-agentcore"
                    }
                }
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:GetResourceApiKey"
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{region}:{account}:token-vault/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:token-vault/default/apikeycredentialprovider/*",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:workload-identity-directory/default/workload-identity/stock_research_agent*"
                ],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:GetResourceOauth2Token"
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{region}:{account}:token-vault/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:token-vault/default/oauth2credentialprovider/*",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:workload-identity-directory/default/workload-identity/stock_research_agent*"
                ],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{region}:{account}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account}:workload-identity-directory/default/workload-identity/stock_research_agent*"
                ],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ApplyGuardrail"
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*:*:inference-profile/*",
                    f"arn:aws:bedrock:{region}:{account}:*"
                ],
            )
        )


        # Create the AgentCore Runtime with IAM authentication
        agentcore_runtime = bedrockagentcore.CfnRuntime(
            self,
            "StockResearchAgentCoreRuntime",
            agent_runtime_name="stock_research_agent",
            description="Stock Research agent with IAM authentication",
            role_arn=execution_role.role_arn,
            agent_runtime_artifact=bedrockagentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration = bedrockagentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=docker_image.image_uri,
                )
            ),
            environment_variables={
                "AWS_REGION": region,
                "AWS_DEFAULT_REGION": region,
                "CREWAI_DISABLE_TELEMETRY": "true",
                "LITELLM_LOCAL_MODEL_COST_MAP": "true",
                "OTEL_TRACES_SAMPLER": "always_on",
                "OTEL_LOG_LEVEL": "debug",
                "SERPER_API_KEY": _serper_api_key,
                "LARGE_MODEL_ID": "bedrock/us.anthropic.claude-sonnet-4-6"
            },
            network_configuration=bedrockagentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"
            )
        )

        # Ensure the runtime is created only after the role and its policies are fully attached
        agentcore_runtime.node.add_dependency(execution_role)

        # Using the DEFAULT endpoint. AgentCore automatically routes to the latest version.
        
        # Outputs
        CfnOutput(
            self,
            "AgentCoreRuntimeArn",
            value=agentcore_runtime.attr_agent_runtime_arn,
            description="ARN of the AgentCore Runtime",
            export_name="AgentCoreRuntimeArn"
        )
        
        CfnOutput(
            self,
            "AgentCoreRuntimeId",
            value=agentcore_runtime.attr_agent_runtime_id,
            description="ID of the AgentCore Runtime",
        )

        CfnOutput(
            self,
            "ECRRepositoryUri",
            value=docker_image.repository.repository_arn,
            description="ECR Repository ARN for the agent container",
        )

        CfnOutput(
            self,
            "ExecutionRoleArn",
            value=execution_role.role_arn,
            description="ARN of the AgentCore Execution Role",
        )