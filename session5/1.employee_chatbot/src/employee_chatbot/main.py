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

def run():
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    employee_id = "sinma04"
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)

    while True:
        query = console.input("[bold blue]You:[/bold blue] ")
        if query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            break

        conversationHistory = memoryUtils.loadShortTermMemory(5)
        userPreferences = memoryUtils.extractPreferences()

        inputs = {
            'employee_query': query,
            'employee_id': employee_id,
            'conversationHistory': conversationHistory,
            'userPreferences': userPreferences
        }

        try:
            crew = createCrew()
            instrument_crewai()
            response = crew.kickoff(inputs=inputs).raw
            memoryUtils.saveMemory(userPrompt=query, assistantResponse=response)
            console.print("\n[bold green]Chatbot:[/bold green]")
            console.print(Markdown(response))
            console.print("\n" + "-"*50 + "\n")
        except Exception as e:
            console.print(f"[bold red]An error occurred while running the crew: {e}[/bold red]")

if __name__ == "__main__":
    run()
