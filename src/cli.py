import sys
import os

# Ensure the root project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from rich.console import Console
from rich.panel import Panel
from src.core.pipeline import CognitivePipeline

console = Console()

def _initialize_pipeline():
    try:
        return CognitivePipeline()
    except Exception as e:
        console.print(f"[bold red]System Offline:[/bold red] {e}\n[dim]Run 'python scripts/setup_models.py' if models are missing.[/dim]")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AlphaEdge Cognitive CLI")
    parser.add_argument("query", type=str, nargs="?", help="The problem you want the Cognitive Loop to solve.")
    parser.add_argument("--live", action="store_true", help="Start the continuous Voice Agent mode.")
    args = parser.parse_args()
    
    if args.live:
        from src.voice.listener import EdgeListener
        from src.voice.speaker import EdgeSpeaker
        listener = EdgeListener()
        speaker = EdgeSpeaker()
        
        console.print(Panel("[bold red]🎙️ LIVE VibeVoice MODE ACTIVE[/bold red]\nSpeak to the system naturally. Press Ctrl+C to stop.", border_style="red"))
        pipeline = _initialize_pipeline()
            
        while True:
            try:
                user_audio_text = listener.listen_once()
                if not user_audio_text:
                    continue
                
                # UX Latency Trick
                speaker.speak_thought_marker()
                
                state = pipeline.run(user_audio_text)
                
                console.print(Panel(state.synthesized_result, border_style="green", title="AlphaEdge Speaks"))
                speaker.speak(state.synthesized_result, sync=True)
            except KeyboardInterrupt:
                console.print("\n[dim]Turning off microphone...[/dim]")
                break
            except Exception as e:
                console.print(f"[bold red]\nVoice Loop Error:[/bold red] {e}")

    elif not args.query:
        # Interactive mode
        console.print(Panel("[bold cyan]🔹 alphaEdge Cognitive CLI[/bold cyan]\nType 'exit' to quit. (Zero-Latency Edge AI)", border_style="cyan"))
        pipeline = _initialize_pipeline()
            
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
        pipeline = _initialize_pipeline()
        state = pipeline.run(args.query)
        console.print(Panel(state.synthesized_result, border_style="green", title="AlphaEdge Synthesis"))

if __name__ == "__main__":
    main()
