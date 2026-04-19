# Session 2 — Assignments

## Assignment 1: Stock Research Crew Variants

**Project:** [1.stockresearch/](1.stockresearch/)

The stock research project ships three crew configurations. Your assignment is to run all three and compare their behaviour.

### Tasks

1. Follow the [installation and configuration steps](1.stockresearch/README.md#installation) to set up your `.env` file with a model, Serper, and Langfuse keys.

2. Run the **single agent crew** by updating the import in [src/stockresearch/main.py](1.stockresearch/src/stockresearch/main.py):
   ```python
   from . crew import crew
   ```
   Run it and observe the trace in Langfuse.

3. Switch to the **multi-agent crew**:
   ```python
   from . crewMultiAgent import crew
   ```
   Run it against the same query and compare the number of LLM calls and agent handoffs in Langfuse.

4. Switch to the **multi-agent crew with planning**:
   ```python
   from . crewWithPlanner import crew
   ```
   Run it and observe how the planner step affects the trace structure.

### Questions to Reflect On

- How does the number of LLM calls differ across the three crews?
- Does the multi-agent crew produce help in any way as compared to single agent?
- What is the trade-off between using a planning and running without one?

---

## Assignment 2: Deep Research Variants

**Project:** [2.deepresearch/](2.deepresearch/)

The deep research project implements two orchestration patterns for a planner → researcher → writer → critic pipeline. Your assignment is to run both and understand how control flow differs.

### Tasks

1. Follow the [installation and configuration steps](2.deepresearch/README.md#installation) to set up your `.env` with a model and Tavily and Langfuse keys.

2. Run the **hierarchical crew** by updating [src/deepresearch/main.py](2.deepresearch/src/deepresearch/main.py):
   ```python
   response = crew.kickoff(inputs=inputs).raw
   ```
   Observe how the manager agent delegates each step at runtime.

3. Switch to the **fixed flow**:
   ```python
   response = await DeepResearchFlow().kickoff_async(inputs=inputs)
   ```
   Observe the explicit step-by-step execution in Langfuse, including parallel sub-question research.

4. Change the `user_query` in `main.py` to a topic of your choice and run both patterns again.

### Questions to Reflect On

- In the hierarchical crew, does the manager always follow the expected order (plan → research → write → critique)? What happens if it doesn't? Does it cost more than fixed flow?
- In the fixed flow, sub-questions are researched in parallel (`asyncio.gather`). Does this produce noticeably faster results?
- Which pattern gives you more confidence that every step was executed? Why?

---

## Assignment 3: Deploy Stock Research to AgentCore

**Project:** [3.stockresearch_infra/](3.stockresearch_infra/)

Your assignment is to package the stock research agent as a Docker container and deploy it to Amazon Bedrock AgentCore Runtime using CDK.

### Tasks

1. Ensure you have the [prerequisites](3.stockresearch_infra/README.md#prerequisites) installed: AWS CLI, CDK v2, UV, and Docker.

2. Make sure `../1.stockresearch/.env` exists and contains a valid `SERPER_API_KEY` — the CDK stack reads it directly.

3. Bootstrap CDK in your account (first time only):
   ```bash
   cdk bootstrap
   ```

4. Deploy the stack:
   ```bash
   uv run cdk deploy
   ```
   Note the `AgentCoreRuntimeId` from the outputs.

5. Invoke the deployed agent using the AWS CLI:
   ```bash
   aws bedrock-agentcore invoke-agent-runtime \
     --agent-runtime-id <RUNTIME_ID> \
     --payload '{"prompt": "What is the current stock price of Tesla?"}' \
     --region us-east-1
   ```

6. Tear down the stack when done:
   ```bash
   uv run cdk destroy
   ```

### Questions to Reflect On

- What advantages does deploying to AgentCore give you over running the agent locally? Think about scalability, access control, and operational overhead.
- Navigate to the AgentCore Runtime in the AWS Console. What built-in **metrics** are available (e.g. invocation count, latency, errors)? How would these help you monitor a production agent?
- Open **CloudWatch Logs** for the runtime. What does the container log on startup (hint: look at what `agentCoreHandler.py` prints)? How would you use these logs to debug a failed invocation?
