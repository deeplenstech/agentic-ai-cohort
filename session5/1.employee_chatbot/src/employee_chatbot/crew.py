import os
from crewai import Agent, Crew, Task, LLM
from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import
from .tools import insert_leave, read_leaves, get_current_date
from crewai_tools import BedrockKBRetrieverTool
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

knowledge_completeness_metric = GEval(
    name="Knowledge Based Completeness",
    criteria="Determine if the retrieved context is complete and contains all necessary information to answer the user's query.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.5
)

def createCrew():
    kb_tool = BedrockKBRetrieverTool(knowledge_base_id=os.environ["BEDROCK_KB_ID"])
    # Surgical injection to bypass Pydantic and enable tracing
    object.__setattr__(kb_tool, "metrics", [knowledge_completeness_metric])
    
    employee_query_agent = Agent(
        role="HR & Leave Manager",
        goal="Answer queries on company policies, accept leave requests from employees, and provide information on leaves availed.",
        backstory=(
            "You're a seasoned HR & Leave Manager. You politely reply to queries from employees "
            "pertaining to employee policies. You also seamlessly handle leave applications, inserting them into "
            "the database, and can quickly pull up records of how many leaves an employee has already taken."
        ),
        llm=LLM(model=os.environ["LARGE_MODEL_ID"], temperature=0),
        tools=[
            kb_tool,
            insert_leave,
            read_leaves,
            get_current_date
        ]
    )

    employee_query_task = Task(
        description=(
            "Handle the following types of tasks from employees: \n"
            "1. Information about company policies (e.g., leave policy, work hours). \n"
            "2. Requesting leave (e.g., 'I want to take leave on [date(s)]'). \n"
            "3. Query about leaves already availed (e.g., 'How many leaves have I taken?').  \n"
            "When an employee requests leave, you MUST use the `insert_leave` tool with the: \n"
            "- Employee ID: {employee_id}  \n"
            "- Start date \n"
            "- End date \n"
            "- Leave type \n"
            "If the user asks how many leaves they have already taken, use the `read_leaves` tool. \n"
            "For general policy questions, use the knowledge base. \n"
            "Always be polite and concise. \n\n"
            "EMPLOYEE_QUERY: {employee_query} \n\n"
            "CONVERSATION_HISTORY: {conversationHistory} \n\n"
            "CONVERSATION_SUMMARY: {conversationSummary} \n\n"
        ),
        expected_output=(
            "An concise answer to the employee query in plain text. The response should be "
            "empathetic, and polite irrespective of the frustration level of the employee"
        ),
        agent=employee_query_agent
    )

    return Crew(
        agents=[employee_query_agent],
        tasks=[employee_query_task],
        verbose=False
    )

