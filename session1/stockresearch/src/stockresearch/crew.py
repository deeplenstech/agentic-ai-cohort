import os
from crewai import Agent, Crew, Task
from crewai_tools import SerperDevTool
from stockresearch.tools.date_tool import GetCurrentDateTool
from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import

stock_researcher = Agent(
    role="Senior Stock Researcher",
    goal="Research on the changes in a stock over period of time as asked by the user",
    backstory=(
        "You're a seasoned stock researcher with a knack for uncovering the latest "
        "developments on a stock. Known for your ability to find the most relevant "
        "information and present it in a clear and concise manner."
    ),
    llm=os.environ["MODEL_ID"],
    tools=[GetCurrentDateTool(), SerperDevTool()]
)

research_task = Task(
    description=(
        "Conduct a thorough research about changes in stock based on user query.\n"
        "USER_QUERY: {user_query}\n"
        "The user query will contain a stock name/ticker and specific dates or a time period.\n"
        "You MUST use your search tools to find the actual stock prices for those exact dates.\n"
        "Do NOT rely on your internal knowledge — always call the search tool to get real data.\n"
        "Find: the stock ticker, old price (at start date), new price (at end date), "
        "the number of days between those dates, and reasons for the price change."
    ),
    expected_output=(
        "A detailed summary with: stock ticker, old price with its date, new price with its date, "
        "number of days between, percentage change, and reasons for the price movement."
    ),
    agent=stock_researcher
)

crew = Crew(
    agents=[stock_researcher],
    tasks=[research_task],
    verbose=True
)
