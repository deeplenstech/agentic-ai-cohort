import os
from crewai import Agent, Crew, Task, LLM
from .utils import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import
from .tools import InsertLeaveTool, ReadLeavesTool, GetCurrentDateTool
from .utils.guardrailUtils import register_guardrail_hooks
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
    register_guardrail_hooks()
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
            "System Constraints: \n"
            "1. Employee should not be able to apply for leaves for another employee or ask to check leave status for another"
            "employee, refuse politely and inform them that you can only access leave information for the "
            "employee ID provided.\n"
            "2. If an employee wants to apply for leaves more than allowed as per policy, there is no way you can "
            "provide exception. \n"
            "3. When applying for leaves, first check the calendar year of leave and type of the leave. "
            "Then check how many leaves of that type are allowed in a calendar year. Then read leaves taken "
            "by the employee based on the leave type. And then check if after the new leaves, would employee "
            "exceed with the allowed leaves based on the leave type. If the new leaves exceed the allowed leaves, "
            "inform the employee and do not insert the leave. If the new leaves do not exceed the allowed leaves, "
            "inform the employee and insert the leaves. \n"
        ),
        llm=LLM(model=os.environ["MODEL_ID"], temperature=0),
        tools=[
            kb_tool,
            InsertLeaveTool(),
            ReadLeavesTool(),
            GetCurrentDateTool()
        ]
    )

    employee_query_task = Task(
        description=(
            "Handle the following types of tasks from employees: \n"
            "1. Information about company policies (e.g., leave policy, work hours). \n"
            "2. Requesting leave (e.g., 'I want to take leave on [date(s)]'). \n" 
            "3. Query about leaves already availed (e.g., 'How many leaves have I taken?').  \n\n"
            "Employee ID: {employee_id} \n\n"
            "EMPLOYEE QUERY: {employee_query} \n\n"
            "CONVERSATION HISTORY in reverse chronological order: {conversationHistory} \n\n"
            "Conversation history can be used to provide context aware responses.\n"
        ),
        expected_output=(
            "A crisp and concise answer to the employee query"
        ),
        agent=employee_query_agent
    )

    return Crew(
        agents=[employee_query_agent],
        tasks=[employee_query_task],
        verbose=True
    )

