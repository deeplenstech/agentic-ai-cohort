# Employee Chatbot: Policy & Leave Manager

## Purpose

Welcome to the **Employee Chatbot** project, powered by [crewAI](https://crewai.com) and [DeepEval](https://github.com/confident-ai/deepeval).

This project features a simple HR agent capable of:
1.  **Policy Querying**: Answering questions about company policies by searching an **Amazon Bedrock Knowledge Base**.
2.  **Leave Management**: Handling leave applications and querying leave history using a local SQLite database (`leaves.db`).
3.  **Conversational Memory**: Maintaining context across multiple turns using short-term memory and automated summaries.

## Features

- **Multi-turn Support**: The chatbot tracks conversation history and maintains a summary to provide contextually aware responses.
- **Tool Augmentation**: 
  - `BedrockKBRetrieverTool`: Searches the employee handbook.
  - `insert_leave`: Records new leave requests in the database.
  - `read_leaves`: Retrieves an employee's leave records.
  - `get_current_date`: Provides the current date for date-relative queries.
- **Online Evaluation**: Live metrics (e.g., Knowledge Based Completeness) are reported to [Confident AI](https://www.confident-ai.com/) during interaction.
- **Offline Testing**: Comprehensive test suite for single-turn and multi-turn scenarios using DeepEval's `ConversationSimulator`.

## Installation

Ensure you have Python >=3.12 <3.13 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

1.  **Install UV** (if not already installed):
    ```bash
    pip install uv
    ```
2.  **Install Dependencies**:
    ```bash
    uv sync
    ```

## Configuration

Copy the template and fill in your credentials:

```bash
cp .env.template .env
```

### Required Environment Variables

| Variable | Description |
| :--- | :--- |
| `MODEL_ID` | The Bedrock model ID (e.g., `bedrock/us.anthropic.claude-3-5-sonnet-20240620-v1:0`). |
| `BEDROCK_KB_ID` | The ID of your Amazon Bedrock Knowledge Base (setup similarly to Session 3 assignments). |
| `CONFIDENT_API_KEY` | Your API key from [Confident AI](https://www.confident-ai.com/) (ensure it's for a specific project). |
| `OPENAI_API_KEY` | Required by DeepEval for running certain metrics (GEval, etc.). |

> [!NOTE]
> Ensure your AWS credentials are configured (via `~/.aws/credentials` or environment variables) with permissions for Bedrock and the Knowledge Base.

---

## Assignment 1: AWS AgentCore Memory Setup

### Goal
Configure the chatbot to use **Amazon Bedrock AgentCore** for persistent conversational memory, allowing it to maintain context across sessions via short-term turns and long-term summaries.

### Steps
1.  **AWS Console Setup**:
    - Navigate to the **Amazon Bedrock AgentCore** console.
    - Under **Build**, find **Memory**
    - Create a new **Memory** and note down the `MEMORY_ID`.
    - Configure a **Memory Strategy** for automated summarization and note down the `MEMORY_SUMMARY_STRATEGY_ID`.
2.  **Environment Configuration**:
    - Update your `.env` file with the retrieved IDs:
      ```env
      MEMORY_ID="your_memory_id"
      MEMORY_SUMMARY_STRATEGY_ID="your_memory_summary_strategy_id"
      ```
3.  **Verify Memory Persistence**:
    - Run the chatbot and have a conversation about a specific topic (e.g., your vacation plans). Try to interact multiple times and see if the chatbot remembers the previous messages and provides relevant responses.
    ```bash
    uv run python -m src.employee_chatbot.main
    ```
    - Exit the chatbot by typing `bye`.
4.  **Deep Dive**:
    - Review `src/employee_chatbot/utils/memory.py` to see how `MemoryClient` from `bedrock_agentcore` is used to `create_event`, `get_last_k_turns`, and `retrieve_memories`.
    - Understand the difference between **Short-term Memory** (exact last $K$ turns) and **Long-term Memory** (summaries extracted via memory strategies).

---

## Assignment 2: Online Evaluation

### Goal
Configure the chatbot, interact with it across multiple turns, and observe the live traces and online evaluations in Confident AI.

### Steps
1.  **Setup Environment**: Fill in your `.env` file with all required keys (including the Memory IDs from Assignment 1).
2.  **Configure Metric Collections** (Optional):
    - To enable live evaluation of your traces and threads, create two **Metric Collections** in the Confident AI dashboard:
      - **Trace Collection**: Used for single-turn evaluations (live traces).
      - **Thread Collection**: Used for multi-turn evaluations (on session exit).
    - Update your `.env` with the collection names:
      ```env
      DEEPEVAL_TRACE_METRIC_COLLECTION="your_trace_collection_name"  # For single-turn traces
      DEEPEVAL_THREAD_METRIC_COLLECTION="your_thread_collection_name" # For multi-turn threads
      ```
3.  **Run the Chatbot**:
    ```bash
    uv run python -m src.employee_chatbot.main
    ```
4.  **Interact**:
    - Ask a policy question (e.g., "What is the sick leave policy?").
    - Apply for a leave (e.g., "I want to take leave from 20th May to 22nd May for a vacation").
    - Ask about your history (e.g., "How many leaves have I taken so far?").
    - Type `Bye` to exit and trigger thread-level evaluation.
5.  **Observe**:
    - Login to [Confident AI](https://www.confident-ai.com/).
    - Navigate to the **Project** and view the **Traces**.
    - Verify that tool calls are captured and metrics are calculated.

---

## Assignment 3: DeepEval Offline Tests

### Goal
Run automated offline tests to validate the chatbot's performance on single-turn and multi-turn goldens.

### Steps
1.  **Setup Test Cases**:
    - Before running the tests, make sure the deepeval test cases are setup by running. These would create golderns in Confident AI:
      ```bash
      uv run python test/setup_deepeval.py
      ```
2.  **Single-Turn Tests**:
    - Ensure you have a golden dataset named `"Employee Chatbot Goldens"` in Confident AI (or modify `test/test_chatbot.py` to match your dataset alias).
    - Run the tests:
      ```bash
      deepeval test run test/test_chatbot.py
      ```
3.  **Multi-Turn Tests**:
    - Ensure you have a conversational golden dataset named `"Employee Chatbot Multi Turn Goldens"`.
    - Run the multi-turn simulation tests:
      ```bash
      deepeval test run test/test_multi_turn.py
      ```
4.  **Verify Results**:
    - Review the test results in the terminal.
    - Check the **Test Runs** section in Confident AI for detailed breakdowns of metric scores.
