import sys
import os
import uuid
import warnings
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from employee_chatbot.crew import createCrew
from employee_chatbot.utils.memory import MemoryUtils
from deepeval.dataset import EvaluationDataset, Golden

def generate_and_push_dataset():
    console = Console()
    console.print("[bold cyan]Starting Golden Dataset Generation...[/bold cyan]")
    
    # Define a list of test queries to bootstrap the golden dataset
    test_queries = [
        "What is the policy for earned leaves?",
        "How many leaves have I taken so far?",
        "I want to apply for 2 days of sick leave starting tomorrow."
    ]
    
    goldens = []
    
    for query in test_queries:
        console.print(f"\n[bold blue]Processing Query:[/bold blue] {query}")
        
        inputs = {
            'employee_query': query,
            'employee_id': str(uuid.uuid4()),
            'conversationHistory': "",
            'userPreferences': ""
        }
        
        try:
            crew = createCrew()
            # Execute the crew to capture its actual output as our golden baseline
            response = crew.kickoff(inputs=inputs).raw
            
            console.print(f"[bold green]Baseline Response Captured:[/bold green]\n{response}")
            
            # Create a Golden object
            golden = Golden(
                input=query,
                expected_output=response
            )
            goldens.append(golden)
            
        except Exception as e:
            console.print(f"[bold red]An error occurred generating golden for query '{query}': {e}[/bold red]")
            continue

    if not goldens:
        console.print("[bold red]No goldens were generated. Aborting push.[/bold red]")
        return

    # Create the Evaluation Dataset
    console.print("\n[bold cyan]Creating and pushing the EvaluationDataset to Confident AI...[/bold cyan]")
    try:
        dataset = EvaluationDataset(goldens=goldens)
        dataset.push(alias="Employee Chatbot Goldens")
        console.print("[bold green]Successfully pushed 'Employee Chatbot Goldens' dataset to Confident AI![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to push dataset to Confident AI: {e}[/bold red]")

if __name__ == "__main__":
    generate_and_push_dataset()
