import sys
import os

# Ensure the root project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from rich.console import Console
from rich.panel import Panel
from src.core.pipeline import CognitivePipeline

console = Console()

def main():
    parser = argparse.ArgumentParser(description="AlphaEdge Cognitive CLI")
    parser.add_argument("query", type=str, nargs="?", help="The problem you want the Cognitive Loop to solve.")
    args = parser.parse_args()
    
    if not args.query:
        # Interactive mode
        console.print(Panel("[bold cyan]🔹 alphaEdge Cognitive CLI[/bold cyan]\nType 'exit' to quit. (Zero-Latency Edge AI)", border_style="cyan"))
        try:
            pipeline = CognitivePipeline()
        except Exception as e:
            console.print(f"[bold red]System Offline:[/bold red] {e}\n[dim]Run 'python scripts/setup_models.py' if models are missing.[/dim]")
            return
            
        while True:
            try:
                user_input = console.input("\n[bold green]You:[/bold green] ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("[dim]Shutting down edge intelligence...[/dim]")
                    break
                if not user_input.strip():
                    continue
                state = pipeline.run(user_input)
                console.print(Panel(state.synthesized_result, border_style="green", title="AlphaEdge Synthesis"))
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[bold red]\nLoop Error:[/bold red] {e}")
    else:
        # Single shot
        try:
            pipeline = CognitivePipeline()
            state = pipeline.run(args.query)
            console.print(Panel(state.synthesized_result, border_style="green", title="AlphaEdge Synthesis"))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}\n[dim]Run 'python scripts/setup_models.py' if models are missing.[/dim]")

if __name__ == "__main__":
    main()
