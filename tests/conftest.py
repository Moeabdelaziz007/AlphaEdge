import sys
from unittest.mock import MagicMock

# Mock all dependencies that are not available in the environment
mock_llama_cpp = MagicMock()
sys.modules["llama_cpp"] = mock_llama_cpp

mock_sqlite_vec = MagicMock()
sys.modules["sqlite_vec"] = mock_sqlite_vec

mock_pydantic = MagicMock()
sys.modules["pydantic"] = mock_pydantic

mock_rich = MagicMock()
sys.modules["rich"] = mock_rich
sys.modules["rich.console"] = MagicMock()

mock_huggingface_hub = MagicMock()
sys.modules["huggingface_hub"] = mock_huggingface_hub

mock_fastapi = MagicMock()
sys.modules["fastapi"] = mock_fastapi

mock_uvicorn = MagicMock()
sys.modules["uvicorn"] = mock_uvicorn

mock_speech_recognition = MagicMock()
sys.modules["SpeechRecognition"] = mock_speech_recognition

mock_pyaudio = MagicMock()
sys.modules["pyaudio"] = mock_pyaudio

mock_torch = MagicMock()
sys.modules["torch"] = mock_torch

mock_transformers = MagicMock()
sys.modules["transformers"] = mock_transformers

mock_diffusers = MagicMock()
sys.modules["diffusers"] = mock_diffusers

mock_librosa = MagicMock()
sys.modules["librosa"] = mock_librosa
