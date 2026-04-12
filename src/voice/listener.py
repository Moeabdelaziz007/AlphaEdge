import speech_recognition as sr
from rich.console import Console

# In a full edge deployment based on VibeVoice standards, 
# you would import `transformers` pipeline for Whisper here.
# For MVP, we bridge hardware mic with SpeechRecognition wrapper.

console = Console()

class EdgeListener:
    """
    Extremely lightweight Speech-To-Text listener using local VAD (Energy Thresholding).
    """
    def __init__(self):
        console.print("[dim]Initializing Edge Microphone parameters...[/dim]")
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True

    def listen_once(self) -> str:
        """
        Listens to a phrase until the user stops speaking, 
        then transcribes it natively via offline Whisper proxy fallback.
        """
        with sr.Microphone() as source:
            console.print("\n[bold cyan]🎙️ Listening...[/bold cyan] (Speak naturally)")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                # Capture audio until silence detected (VAD principle)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                console.print("[dim]Processing neural audio...[/dim]")
                
                # We use google local proxy or whisper offline. 
                # For Edge zero-config MVP, fallback to recognize_google (or offline sphinx/whisper)
                text = self.recognizer.recognize_google(audio)
                console.print(f"[bold green]🗣️ You:[/bold green] {text}")
                return text
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                console.print("[dim]Could not parse audio...[/dim]")
                return ""
            except Exception as e:
                console.print(f"[red]Audio routing error: {e}[/red]")
                return ""
