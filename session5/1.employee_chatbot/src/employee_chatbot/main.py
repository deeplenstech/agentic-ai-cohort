#!/usr/bin/env python
import warnings
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from . crew import createCrew
from rich.console import Console
from rich.markdown import Markdown
import uuid
from .utils.memory import MemoryUtils
from deepeval.integrations.crewai import instrument_crewai
from deepeval.tracing import trace, update_current_trace, evaluate_thread
from deepeval.metrics import BaseMetric
from deepeval.metrics import TaskCompletionMetric
from deepeval.metrics import StepEfficiencyMetric
from .deepeval_patch import apply_deepeval_patch

instrument_crewai()
apply_deepeval_patch()

def run():
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    employee_id = console.input("[bold yellow]Enter your Employee ID:[/bold yellow] ").strip()
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)

    while True:
        query = console.input("[bold blue]You:[/bold blue] ")
        if query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            # Trigger thread-level evaluation on exit
            # Ensure you have created a Multi-turn Metric Collection in Confident AI
            evaluate_thread(
                thread_id=session_id, 
                metric_collection="employee_chatbot_multi_turn" 
            )
            break

        try:
            with trace(thread_id=session_id, user_id=employee_id, input=query, name="Employee Chatbot Interaction", metric_collection="employee_chatbot"):
                conversationHistory = memoryUtils.loadShortTermMemory(5)
                conversationSummary = memoryUtils.extractSummary()
                inputs = {
                    'employee_query': query,
                    'employee_id': employee_id,
                    'conversationHistory': conversationHistory,
                    'conversationSummary': conversationSummary
                }
                crew = createCrew()
                response = crew.kickoff(inputs=inputs).raw
                update_current_trace(output=response)
                
                memoryUtils.saveMemory(userPrompt=query, assistantResponse=response)
                console.print("\n[bold green]Chatbot:[/bold green]")
                console.print(Markdown(response))
                console.print("\n" + "-"*50 + "\n")
        except Exception as e:
            console.print(f"[bold red]An error occurred while running the crew: {e}[/bold red]")

if __name__ == "__main__":
    run()
