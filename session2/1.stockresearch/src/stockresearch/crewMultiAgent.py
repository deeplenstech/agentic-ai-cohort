import os
from crewai import Agent, Crew, Task, LLM
from pydantic import BaseModel, Field
from crewai_tools import SerperDevTool
from . tools.date_tool import GetCurrentDateTool
from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import


class StockResearchOutput(BaseModel):
    old_price: float = Field(description="Stock price at the start")
    new_price: float = Field(description="Stock price at the end")
    percent_change: float = Field(description="Percentage change")
    potential_reason: str = Field(description="Brief explanation of what drove the price change")
    days_between: int = Field(description="Number of days between old price and new price")
    stock_ticker: str = Field(description="The stock ticker symbol, e.g. AAPL, as asked by user")

stock_researcher = Agent(
    role="Senior Stock Researcher",
    goal="Research on the changes in a stock over period of time as asked by the user",
    backstory=(
        "You're a seasoned stock researcher with a knack for uncovering the latest "
        "developments on a stock. Known for your ability to find the most relevant "
        "information and present it in a clear and concise manner."
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
    tools=[GetCurrentDateTool(), SerperDevTool()]
)

report_creator = Agent(
    role="Senior Report Creator",
    goal="Creates a report based on the desired report structure",
    backstory=(
        "You're a seasoned report creator with a knack for creating well structured report "
        "based on the provided unstructured report and the final report structure."
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"])
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

format_task = Task(
    description=(
        "Using the research findings provided, format the data into the required JSON schema.\n"
        "Do not perform any new research — only structure what was already found."
    ),
    expected_output="A JSON object matching the StockResearchOutput schema.",
    output_json=StockResearchOutput,
    agent=report_creator,
    context=[research_task]
)

crew = Crew(
    agents=[stock_researcher, report_creator],
    tasks=[research_task, format_task],
    verbose=True
)
