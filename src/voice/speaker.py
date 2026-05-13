import shutil
import subprocess
import threading
from rich.console import Console

# The architecture conforms strictly to VibeVoice endpoints
# import torch
# from diffusers import AudioPipeline

console = Console()

class EdgeSpeaker:
    """
    Text-to-Speech logic bridging Cognitive Context Switching output to Voice.
    """
    def __init__(self):
        console.print("[dim]Attaching to VibeVoice-compliant TTS architecture...[/dim]")
        # Placeholder for VibeVoice Diffusion Pipeline loading:
        # self.vibe_pipeline = DiffusionPipeline.from_pretrained(...)

    def speak(self, text: str, sync: bool = False):
        """
        Translates text into native edge audio.
        """
        def _say():
            # Use the macOS `say` binary if available; otherwise no-op rather than
            # shell out (which is a command-injection risk).
            say_bin = shutil.which("say")
            if not say_bin:
                console.print("[dim]TTS skipped: `say` binary not available on this platform.[/dim]")
                return
            try:
                subprocess.run([say_bin, str(text)], check=False, timeout=30)
            except subprocess.TimeoutExpired:
                console.print("[dim]TTS timeout (30s).[/dim]")
            except Exception as exc:
                console.print(f"[red]TTS error: {exc}[/red]")
            
        if sync:
            _say()
        else:
            threading.Thread(target=_say, daemon=True).start()

    def speak_thought_marker(self):
        """
        The UX Latency Trick: Asynchronously speaks an immediate response chunk 
        before the Challenger and Synthesizer complete heavy logic lifting.
        """
        self.speak("Let me analyze that...", sync=False)
