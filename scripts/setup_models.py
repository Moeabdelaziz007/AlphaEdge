import os
from huggingface_hub import hf_hub_download
from rich.console import Console

console = Console()

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# Strict offline caching models 
MODELS_TO_DOWNLOAD = [
    {
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "description": "Primary Intelligence (Generator/Challenger/Synthesizer)"
    },
    {
        "repo_id": "nomic-ai/nomic-embed-text-v1.5-GGUF",
        "filename": "nomic-embed-text-v1.5.Q4_K_M.gguf",
        "description": "Vector Memory Embedding Model"
    }
]

def download_models():
    console.print("[bold cyan]🚀 Initializing Offline Model Setup...[/bold cyan]")
    console.print("This script establishes extreme edge privacy via localized caching.\n")
    
    for model in MODELS_TO_DOWNLOAD:
        console.print(f"📡 Fetching [bold yellow]{model['filename']}[/bold yellow] ({model['description']})...")
        
        target_path = os.path.join(MODELS_DIR, model['filename'])
        if os.path.exists(target_path):
            console.print(f"[bold green]✅ Cached locally:[/bold green] {target_path}\n")
            continue
            
        try:
            file_path = hf_hub_download(
                repo_id=model["repo_id"],
                filename=model["filename"],
                local_dir=MODELS_DIR,
                local_dir_use_symlinks=False
            )
            console.print(f"[bold green]✅ Download Secure:[/bold green] {file_path}\n")
        except Exception as e:
            console.print(f"[bold red]❌ Failed to download {model['filename']}:[/bold red] {str(e)}")

    console.print("[bold cyan]✅ Setup complete. The Cognitive Engine is ready for zero-latency execution.[/bold cyan]")

if __name__ == "__main__":
    download_models()
