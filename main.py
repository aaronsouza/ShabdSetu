# main.py

import io
import numpy as np
import torch
import noisereduce as nr
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from pydub import AudioSegment

# Import our new evaluation logic
from pronunciation_evaluator import evaluate_pronunciation

# -----------------
# 1. APP INITIALIZATION & MODEL LOADING
# -----------------

app = FastAPI(
    title="Language Learning AI API",
    description="API for real-time speech-to-text and pronunciation evaluation.",
    version="2.0.0"
)

ASR_MODELS = {}
SUPPORTED_LANGUAGES = {
    # For now, we only load the local Hindi model for evaluation
    "hi": "./indicwav2vec-hindi",
}

# This is a mock database of target phrases for the user to practice.
# In a real app, you would fetch this from a PostgreSQL database.
MOCK_PHRASE_DB = {
    "HIN_001": "नमस्ते आप कैसे हैं",
    "HIN_002": "मेरा नाम आरव है",
    "HIN_003": "नमस्ते",
    "HIN_004": "यह एक सुंदर दिन है"
}


@app.on_event("startup")
async def load_models():
    print("Loading ASR models...")
    for lang_code, model_name in SUPPORTED_LANGUAGES.items():
        try:
            # We assume the model is local and don't need a token
            processor = Wav2Vec2Processor.from_pretrained(model_name)
            model = Wav2Vec2ForCTC.from_pretrained(model_name)
            ASR_MODELS[lang_code] = {"processor": processor, "model": model}
            print(f"Successfully loaded model for language: {lang_code}")
        except Exception as e:
            print(f"Error loading model for {lang_code}: {e}")
    print("All models loaded successfully!")


# -----------------
# 2. AUDIO PRE-PROCESSING & TRANSCRIPTION LOGIC (from Task 1)
# -----------------

def preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_frame_rate(target_sr)
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32768.0
        reduced_noise_audio = nr.reduce_noise(y=samples, sr=target_sr, prop_decrease=0.8)
        return reduced_noise_audio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")


def transcribe_audio_data(audio_data: np.ndarray, lang: str) -> str:
    """Helper function to perform transcription on pre-processed audio data."""
    if lang not in ASR_MODELS:
        raise HTTPException(status_code=400, detail=f"Unsupported language '{lang}'.")

    try:
        processor = ASR_MODELS[lang]["processor"]
        model = ASR_MODELS[lang]["model"]
        inputs = processor(audio_data, sampling_rate=16000, return_tensors="pt", padding=True)

        with torch.no_grad():
            logits = model(inputs.input_values, attention_mask=inputs.attention_mask).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)[0]
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


# -----------------
# 3. NEW PRONUNCIATION EVALUATION ENDPOINT
# -----------------

@app.post("/api/v1/learning/evaluate")
async def evaluate_user_pronunciation(
        lang: str = Form(..., description="Language code (e.g., 'hi')"),
        phrase_id: str = Form(..., description="The ID of the phrase to evaluate against (e.g., 'HIN_001')"),
        audio_file: UploadFile = File(..., description="User's audio recording of the phrase.")
):
    """
    Accepts user audio, transcribes it, and evaluates pronunciation against a target phrase.
    """
    # 1. Fetch the correct target phrase from our "database"
    target_phrase = MOCK_PHRASE_DB.get(phrase_id)
    if not target_phrase:
        raise HTTPException(status_code=404, detail=f"Phrase ID '{phrase_id}' not found.")

    # 2. Process and transcribe the user's audio (reusing our logic from Task 1)
    contents = await audio_file.read()
    processed_audio = preprocess_audio(contents)
    transcribed_text = transcribe_audio_data(processed_audio, lang)

    if not transcribed_text:
        # Handle cases where transcription returns nothing
        return {
            "transcription": "",
            "target_phrase": target_phrase,
            "score": 0,
            "feedback": "We couldn't hear you clearly. Please try speaking louder."
        }

    # 3. Call our new evaluator to get the score and feedback
    evaluation = evaluate_pronunciation(transcribed_text, target_phrase, lang)

    # 4. Return the complete evaluation
    return evaluation


# -----------------
# 4. ROOT ENDPOINT
# -----------------

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Language Learning AI API! Use the /evaluate endpoint."}