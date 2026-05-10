💻 Getting Started
Clone the repository to your local machine before starting the assignments: `git clone https://github.com/deeplenstech/agentic-ai-cohort.git`

📚 Session 5 Assignments
This session covers the architecture of a production-grade HR Chatbot. You will implement persistent conversational memory using AWS Bedrock AgentCore and establish a rigorous evaluation framework (both online and offline) using DeepEval and Confident AI.
🔗 [Session 5 README](https://github.com/deeplenstech/agentic-ai-cohort/blob/main/session5/1.employee_chatbot/README.md)

🧠 Assignment 1 — AWS AgentCore Memory Setup
Configure the chatbot to use **Amazon Bedrock AgentCore** for persistent memory. You will set up Memory Storage and Summarization Strategies in the AWS Console to allow the agent to maintain context across different sessions. This assignment explores the practical implementation of **Short-term Memory** (recent turns) and **Long-term Memory** (automated summaries).
🔗 [Assignment 1 Details](https://github.com/deeplenstech/agentic-ai-cohort/blob/main/session5/1.employee_chatbot/README.md#assignment-1-aws-agentcore-memory-setup)

🤖 Assignment 2 — Configure and Run Employee Chatbot
Run the HR agent and observe its decision-making in real-time. You will configure **Confident AI** to capture live traces and calculate online metrics (like Knowledge Based Completeness) as you interact with the bot. This assignment demonstrates how to bridge the gap between local development and production-grade observability.
🔗 [Assignment 2 Details](https://github.com/deeplenstech/agentic-ai-cohort/blob/main/session5/1.employee_chatbot/README.md#assignment-2-configure-and-run-employee-chatbot)

🧪 Assignment 3 — DeepEval Offline Tests
Validate the chatbot's performance using automated testing. You will bootstrap golden datasets (both single-turn and multi-turn) and execute a full test suite using `deepeval test run`. Use the **Conversation Simulator** to stress-test multi-turn logic and review detailed metric breakdowns in the Confident AI dashboard to ensure your agent is reliable and accurate.
🔗 [Assignment 3 Details](https://github.com/deeplenstech/agentic-ai-cohort/blob/main/session5/1.employee_chatbot/README.md#assignment-3-deepeval-offline-tests)
