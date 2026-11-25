import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
BIN_DIR = ROOT_DIR / "bin"
TEMPLATES_DIR = ROOT_DIR / "templates"

@dataclass
class HyperConfig:
    # LLM Settings (Universal FreeLLMAPI / OpenAI / Gemini / Ollama)
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # openai, gemini, ollama, custom
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")       # e.g., http://localhost:8080/v1 or custom FreeLLMAPI
    llm_api_key: str = os.getenv("LLM_API_KEY", "")         # API key or dummy key
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Model name expected by endpoint
    
    # Transcription Settings
    transcription_device: str = os.getenv("TRANSCRIPTION_DEVICE", "cuda") # cuda or cpu
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")               # tiny, base, small, medium, large-v3
    
    # Video & Layout Settings
    output_height: int = 1920
    output_width: int = 1080
    max_clip_duration: int = int(os.getenv("MAX_CLIP_DURATION", "60"))
    min_clip_duration: int = int(os.getenv("MIN_CLIP_DURATION", "20"))
    default_layout: str = os.getenv("DEFAULT_LAYOUT", "auto")            # auto, solo, podcast_split, gaming_facecam
    
    # Safe zones & Captions
    safe_zone_bottom_margin: int = 240  # Keep clear of TikTok/Reels UI buttons
    safe_zone_top_margin: int = 180     # Keep clear of top overlays
    
    @classmethod
    def load(cls) -> "HyperConfig":
        return cls()
