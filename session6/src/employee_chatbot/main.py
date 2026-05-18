#!/usr/bin/env python
from .agent_v1 import createCrew
from .agent_v3 import EmployeeChatbotFlow
import warnings
import uuid
import os
from deepeval.integrations.crewai import instrument_crewai
from deepeval.tracing import trace, update_current_trace, evaluate_thread
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from .utils.memory import MemoryUtils
from .utils.session import Session
from .agent_v3 import EmployeeChatbotFlow
from .agent_v1 import createCrew as create_crew_v1
from .agent_v2 import createCrew as create_crew_v2

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

instrument_crewai()

def run():
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    employee_id = console.input("[bold yellow]Enter your Employee ID:[/bold yellow] ").strip()
    Session().setEmployeeId(employee_id)
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)

    while True:
        query = console.input("[bold blue]You:[/bold blue] ")
        if query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            break

        try:
            trace_kwargs = {
                "thread_id": session_id,
                "user_id": employee_id,
                "input": query,
                "name": "Employee Chatbot Interaction"
            }

            with trace(**trace_kwargs):
                conversationHistory = memoryUtils.loadShortTermMemory()
                inputs = {
                    'employee_query': query,
                    'employee_id': employee_id,
                    'conversationHistory': conversationHistory if conversationHistory else "No prior conversation history"
                }
                
                agentVersion = os.getenv("AGENT_VERSION", "v1")
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
                
                update_current_trace(output=response)
                
                memoryUtils.saveMemory(userPrompt=query, assistantResponse=response)
                console.print("\n[bold green]Chatbot:[/bold green]")
                console.print(Markdown(response))
                console.print("\n" + "-"*50 + "\n")
        except Exception as e:
            console.print(f"[bold red]An error occurred while running the crew: {e}[/bold red]")

if __name__ == "__main__":
    run()
