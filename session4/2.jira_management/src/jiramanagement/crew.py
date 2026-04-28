import base64
import os
from crewai import Agent, Crew, Task, LLM
from crewai_tools import MCPServerAdapter


def create_crew():
    atlassian_email = os.environ["ATLASSIAN_EMAIL"]
    atlassian_api_key = os.environ["ATLASSIAN_API_KEY"]
    atlassian_token = base64.b64encode(f"{atlassian_email}:{atlassian_api_key}")
    server_params = {
        "url": "https://mcp.atlassian.com/v1/mcp",
        "transport": "streamable-http",
        "headers": {"Authorization": f"Basic {atlassian_token}"},
    }

    tools = MCPServerAdapter(server_params).tools

    jira_manager = Agent(
        role="Jira Project Manager",
        goal=(
            "Manage Jira projects by creating and organising epics, tasks, and sub-tasks "
            "from requirements. Ensure proper dependency tracking, design phase checks for "
            "enhancements, and security review tasks for every enhancement."
        ),
        backstory=(
            "You are a seasoned Jira Project Manager with deep expertise in agile project "
            "management and software delivery. You excel at translating requirements documents "
            "into well-structured Jira epics and tasks with clear acceptance criteria and "
            "dependencies. For any enhancement request, you always evaluate whether it needs "
            "a design phase (e.g., architectural changes, new integrations, significant UX work) "
            "and create a dedicated design task if so. You also enforce that every enhancement "
            "goes through a security review task before being marked ready for development."
        ),
        llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
        tools=tools,
    )

    jira_task = Task(
        description=(
            "Perform the following Jira management action:\n"
            "{jira_request}\n\n"
            "Important guidelines:\n"
            "- For enhancements: assess whether a design phase is required (architectural "
            "  impact, new integrations, significant UI/UX changes). If yes, create a design task.\n"
            "- For enhancements: always create a security review task.\n"
            "- Model task dependencies accurately (e.g., design before implementation, "
            "  security review before QA).\n"
            "- Provide a clear summary of all created items with their IDs and relationships."
        ),
        expected_output=(
            "A structured summary of all Jira items created, including:\n"
            "- Epic: ID, summary, description\n"
            "- Tasks: ID, summary, type, dependencies\n"
            "- Any design or security review tasks added for enhancements"
        ),
        agent=jira_manager,
    )

    return Crew(
        agents=[jira_manager],
        tasks=[jira_task],
        verbose=True,
        planning=True,
        planning_llm=LLM(model=os.environ["LARGE_MODEL_ID"])
    )

