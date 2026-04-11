from crewai import Agent, Crew, Task, LLM

from crewai_tools import SerperDevTool
from stockresearch.tools.date_tool import GetCurrentDateTool

stock_researcher = Agent(
    role="Senior Stock Researcher",
    goal="Research on the changes in a stock over period of time.",
    backstory=(
        "You're a seasoned stock researcher with a knack for uncovering the latest "
        "developments on a stock. Known for your ability to find the most relevant "
        "information and present it in a clear and concise manner."
    ),
    llm="anthropic/claude-sonnet-4-6",
    tools=[GetCurrentDateTool(), SerperDevTool()]
)

research_task = Task(
    description=(
        "Conduct a thorough research about changes in stock based on user query.\n"
        "USER_QUERY: {user_query}\n"
        "Make sure you search and provide the relevant information."
    ),
    expected_output="structured output as mentioned in the task definition.",
    agent=stock_researcher
)

crew = Crew(
    agents=[stock_researcher],
    tasks=[research_task],
    verbose=True,
    tracing=True
)
