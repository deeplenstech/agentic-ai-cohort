import sys
import os
import hashlib
import json
from deepteam import red_team
from deepteam.frameworks import OWASP_ASI_2026
from deepteam.test_case import RTTurn
from dotenv import load_dotenv
from deepteam.attacks.single_turn import Roleplay
from deepteam.attacks.multi_turn import CrescendoJailbreaking
from rich.console import Console
from rich.panel import Panel
import deepteam.red_teamer.api as dt_api
import deepteam.red_teamer.red_teamer as rt_rt

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.employee_chatbot.agent_v3 import EmployeeChatbotFlow
from src.employee_chatbot.agent_v1 import createCrew as create_crew_v1
from src.employee_chatbot.agent_v2 import createCrew as create_crew_v2
from test.utils.tool_tracker import ToolCallTracker
from dotenv import load_dotenv

load_dotenv()
console = Console()

async def callback(input: str, turns: list[RTTurn] = None) -> RTTurn:
    history = "\n".join([
        f"{turn.role}: {turn.content}"
        for turn in (turns or [])
    ])

    first_turn_content = turns[0].content if turns else input
    employee_id = hashlib.sha256(first_turn_content.encode()).hexdigest()

    inputs = {
        'employee_query': input,
        'employee_id': employee_id,
        'conversationHistory': history if history else "No prior conversation history"
    }
    with ToolCallTracker() as tracker:
        console.print(Panel(input, title="[bold blue]🗣️ User Input[/bold blue]", border_style="blue"))
        agentVersion = os.getenv("AGENT_VERSION", "v1")
        console.print(Panel(agentVersion, title="[bold blue]🗣️ Agent Version[/bold blue]", border_style="blue"))
        
        if agentVersion == "v1":
            crew = create_crew_v1()
            response = crew.kickoff(inputs=inputs).raw
        elif agentVersion == "v2":
            crew = create_crew_v2()
            response = crew.kickoff(inputs=inputs).raw
        elif agentVersion == "v3":
            flow = EmployeeChatbotFlow()
            flow.state.employee_query = query
            flow.state.employee_id = employee_id
            flow.state.conversationHistory = str(conversationHistory)
            flow.kickoff()
            response = flow.state.final_response
        console.print(Panel(response, title="[bold green]🤖 Assistant Output[/bold green]", border_style="green"))
        
        return RTTurn(
            role="assistant",
            content=response,
            tools_called=tracker.tool_calls
        )


# Disable pushing results to Confident AI
rt_rt.is_confident = lambda: False