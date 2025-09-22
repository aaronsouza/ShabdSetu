# tts_generator.py

import os
import requests
import wave
from pathlib import Path
from piper import PiperVoice
from fastapi.responses import FileResponse

# --- Configuration ---
# Directory to store the downloaded Piper voice models
MODEL_DIR = Path("./piper_models")
MODEL_DIR.mkdir(exist_ok=True)

# Define the voice models we want to use for each language.
# This has been updated to the "arya" voice model, which is currently available.
VOICE_MODELS = {
    "hi": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/arya/hi_IN-arya-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/arya/hi_IN-arya-medium.onnx.json",
        "model_path": MODEL_DIR / "hi_IN-arya-medium.onnx",
        "config_path": MODEL_DIR / "hi_IN-arya-medium.onnx.json",
    }
}

TTS_PIPER_VOICES = {}

def download_file(url: str, local_path: Path):
    """Downloads a file from a URL to a local path if it doesn't exist."""
    if local_path.exists():
        print(f"✅ Model file already exists: {local_path.name}")
        return
    print(f"Downloading model file: {local_path.name}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅ Download complete: {local_path.name}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download {url}: {e}")

def load_tts_models():
    """Downloads all required TTS models and loads them into memory."""
    print("Loading TTS models...")
    for lang, model_info in VOICE_MODELS.items():
        download_file(model_info["model_url"], model_info["model_path"])
        download_file(model_info["config_url"], model_info["config_path"])

        if model_info["model_path"].exists() and model_info["config_path"].exists():
            try:
                voice = PiperVoice.from_onnx(str(model_info["model_path"]), str(model_info["config_path"]))
                TTS_PIPER_VOICES[lang] = voice
                print(f"✅ Successfully loaded TTS model for language: {lang}")
            except Exception as e:
                print(f"❌ Error loading TTS model for {lang}: {e}")
        else:
            print(f"❌ Cannot load TTS model for {lang}: Model files not found.")

def generate_speech_audio(text: str, language: str) -> FileResponse:
    """
    Generates speech from text using the loaded Piper TTS model
    and returns it as a temporary WAV file response.
    """
    if language not in TTS_PIPER_VOICES:
        raise ValueError(f"No TTS model loaded for language: {language}")

    voice = TTS_PIPER_VOICES[language]
    output_path = Path("temp_tts_output.wav")

    try:
        with wave.open(str(output_path), "wb") as wav_file:
            voice.synthesize(text, wav_file)
        return FileResponse(path=output_path, media_type="audio/wav", filename="pronunciation.wav")
    except Exception as e:
        print(f"❌ Error during speech synthesis: {e}")
        raise ValueError("Failed to generate speech audio.")




