# main.py

import io
import os
import psycopg2
import numpy as np
import torch
import noisereduce as nr
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import StreamingResponse
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from pydub import AudioSegment

# Import our evaluation logic
from pronunciation_evaluator import evaluate_pronunciation
# Import our TTS logic (currently a placeholder)
from tts_generator import load_tts_models, generate_speech_audio

# --- IMPORTANT: PASTE YOUR DATABASE CREDENTIALS HERE ---
DB_HOST = "db.biutmpyotmmsjcnbllff.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "aaronashutosh"
# ---

# -----------------
# 1. APP INITIALIZATION & MODEL LOADING
# -----------------

app = FastAPI(
    title="BisiBaath Dialect AI API",
    description="API for language learning and dialect contribution.",
    version="4.0.0"
)

ASR_MODELS = {}
SUPPORTED_LANGUAGES = {"hi": "./indicwav2vec-hindi"}


# This is the old mock phrase DB. We no longer need it, but keep it for reference.
# MOCK_PHRASE_DB = { ... }

@app.on_event("startup")
async def load_all_models():
    """Load all AI models on server startup."""
    print("Loading ASR models...")
    for lang_code, model_name in SUPPORTED_LANGUAGES.items():
        try:
            processor = Wav2Vec2Processor.from_pretrained(model_name)
            model = Wav2Vec2ForCTC.from_pretrained(model_name)
            ASR_MODELS[lang_code] = {"processor": processor, "model": model}
            print(f"✅ Successfully loaded ASR model for language: {lang_code}")
        except Exception as e:
            print(f"❌ Error loading ASR model for {lang_code}: {e}")

    # Load TTS Models (using the placeholder function)
    load_tts_models()


# -----------------
# 2. HELPER FUNCTIONS (Audio Processing, DB Connection)
# -----------------

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        # In a real app, you might handle this more gracefully
        raise HTTPException(status_code=500, detail="Database connection error.")


def preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_frame_rate(target_sr)
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32768.0
        return nr.reduce_noise(y=samples, sr=target_sr, prop_decrease=0.8)
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
        return processor.batch_decode(predicted_ids)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


# -----------------
# 3. DIALECT CONTRIBUTION ENDPOINT (Task 1 & 2)
# -----------------

@app.post("/api/v1/dialects/contribute")
async def contribute_dialect(
        lang: str = Form(..., description="Language code of the contribution (e.g., 'hi')"),
        user_spelling: str = Form(..., description="The contributor's spelling of the word/phrase."),
        meaning: str = Form(..., description="The meaning of the word/phrase."),
        region: str = Form(..., description="The region where this dialect is used."),
        notes: str = Form(None, description="Any additional context or notes."),
        audio_file: UploadFile = File(..., description="The audio recording of the contribution.")
):
    """
    Handles user-submitted recordings of dialect words or phrases.
    """
    conn = None
    try:
        # --- Task 1: Processing and Storing Contributions ---
        audio_bytes = await audio_file.read()
        processed_audio = preprocess_audio(audio_bytes)
        asr_transcription = transcribe_audio_data(processed_audio, lang)

        user_id = "user_abc_123"  # Hardcoded for now

        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO dialect_contributions 
        (user_id, audio_data, user_spelling, asr_transcription, meaning, region, notes, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id; 
        """
        cur.execute(insert_query, (
            user_id, audio_bytes, user_spelling, asr_transcription,
            meaning, region, notes, 'pending_review', datetime.utcnow()
        ))
        new_contribution_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Contribution {new_contribution_id} saved with status 'pending_review'.")

        # --- Task 2: Developing the "Rarity" Detector ---
        is_rare = False
        check_query = "SELECT COUNT(*) FROM dialect_dictionary WHERE word = %s;"
        cur.execute(check_query, (asr_transcription,))
        count = cur.fetchone()[0]

        if count == 0:
            is_rare = True
            update_query = "UPDATE dialect_contributions SET status = %s WHERE id = %s;"
            cur.execute(update_query, ('pending_expert_validation', new_contribution_id))
            conn.commit()
            print(f"✅ Rare word! Contribution {new_contribution_id} flagged for expert validation.")

        cur.close()

        return {
            "message": "Contribution received successfully!",
            "contribution_id": new_contribution_id,
            "asr_transcription": asr_transcription,
            "is_rare_candidate": is_rare,
            "status": 'pending_expert_validation' if is_rare else 'pending_review'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


# -----------------
# 4. ROOT ENDPOINT
# -----------------

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the BisiBaath Dialect AI API!"}



