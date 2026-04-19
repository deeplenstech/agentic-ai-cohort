import os
from bedrock_agentcore import BedrockAgentCoreApp
from . crewWithPlanner import crew

# Create AgentCore App
app = BedrockAgentCoreApp()

# Print env vars to stdout for CloudWatch diagnostics
print("ENV VARS:", {k: v for k, v in os.environ.items()}, flush=True)

@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")

    if not prompt:
        raise ValueError("Missing required payload parameters")

    inputs = {
        "user_query": prompt
    }

    try:
        # Trigger the Crew
        response = crew.kickoff(inputs=inputs).raw
    except Exception as e:
        response = "An unknown error occurred while processing your request."

    return response
if __name__ == "__main__":
  app.run()