import os
from crewai import Agent, Crew, Task, LLM
from .utils import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import
from .tools import InsertLeaveTool, ReadLeavesTool, GetCurrentDateTool
from crewai_tools import BedrockKBRetrieverTool
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

def createCrew():
    kb_tool = BedrockKBRetrieverTool(knowledge_base_id=os.environ["BEDROCK_KB_ID"])
    
    employee_query_agent = Agent(
        role="HR & Leave Manager",
        goal="Answer queries on company policies, accept leave requests from employees, and provide information on leaves availed.",
        backstory=(
            "You're a seasoned HR & Leave Manager. You politely reply to queries from employees "
            "pertaining to employee policies. You also seamlessly handle leave applications, inserting them into "
            "the database, and can quickly pull up records of how many leaves an employee has already taken."
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
            "2. Requesting leave (e.g., 'I want to take leave on [date(s)]'). When applying for leaves, first check "
            "the calendar year of leave and type of the leave. Then check how many leaves of that type are allowed in a "
            "calendar year. Then read leaves taken by the employee based on the leave type. And then check "
            "if after the new leaves, would employee exceed with the allowed leaves based on the leave type. "
            "If the new leaves exceed the allowed leaves, inform the employee and do not insert the leave. "
            "If the new leaves do not exceed the allowed leaves, inform the employee and insert the leaves. \n"
            "3. Query about leaves already availed (e.g., 'How many leaves have I taken?').  \n\n"
            "Employee ID: {employee_id} \n\n"
            "EMPLOYEE QUERY: {employee_query} \n\n"
            "CONVERSATION HISTORY in reverse chronological order: {conversationHistory} \n\n"
            "Please note to use the conversation history to provide context aware responses.\n\n"
        ),
        expected_output=(
            "A crisp and concise answer to the employee query in plain text. The response should be "
            "empathetic, and polite irrespective of the frustration level of the employee"
        ),
        agent=employee_query_agent
    )

    return Crew(
        agents=[employee_query_agent],
        tasks=[employee_query_task],
        verbose=True
    )

