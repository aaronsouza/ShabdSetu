import io
import psycopg2
import numpy as np
import torch
import noisereduce as nr
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydub import AudioSegment
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Import your custom logic modules
from pronunciation_evaluator import evaluate_pronunciation
from translation_service import TranslationService

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
    title="BhashaBuddy AI API",
    description="A complete API for language learning and dialect documentation.",
    version="4.0.0"
)

# Global variables for our AI models
ASR_MODELS = {}
TRANSLATION_SERVICE = None
SUPPORTED_LANGUAGES = {"hi": "./indicwav2vec-hindi"}

@app.on_event("startup")
async def load_models():
    """Load all AI models into memory on server startup."""
    global TRANSLATION_SERVICE

    print("--- Loading AI Models ---")
    # Load Speech-to-Text (ASR) Model
    print("Loading ASR model...")
    for lang_code, model_name in SUPPORTED_LANGUAGES.items():
        try:
            processor = Wav2Vec2Processor.from_pretrained(model_name)
            model = Wav2Vec2ForCTC.from_pretrained(model_name)
            ASR_MODELS[lang_code] = {"processor": processor, "model": model}
            print(f"✅ Successfully loaded ASR model for language: {lang_code}")
        except Exception as e:
            print(f"❌ Error loading ASR model for {lang_code}: {e}")

    # Load Translation Model
    try:
        TRANSLATION_SERVICE = TranslationService()
        TRANSLATION_SERVICE.load_model()
    except Exception as e:
        print(f"❌ Critical error loading translation service: {e}")
        TRANSLATION_SERVICE = None # Ensure it's None on failure

    print("--- All models loaded ---")

# -----------------
# 2. HELPER FUNCTIONS
# -----------------

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="500: Database connection error.")

def preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """Cleans, standardizes, and converts audio from any format."""
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_frame_rate(target_sr)
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32768.0
        return nr.reduce_noise(y=samples, sr=target_sr, prop_decrease=0.8)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")

def transcribe_audio_data(audio_data: np.ndarray, lang: str) -> str:
    """Performs transcription on pre-processed audio data."""
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
# 3. API ENDPOINTS
# -----------------

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the BhashaBuddy AI API!"}

# --- Part 1: Learning Mode Endpoints ---

@app.get("/api/v1/learning/categories")
def get_all_categories():
    """Fetches all learning categories from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM categories ORDER BY id;")
        categories = [{"id": row[0], "name": row[1], "description": row[2]} for row in cur.fetchall()]
        cur.close()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn: conn.close()

@app.get("/api/v1/learning/lessons/{category_id}")
def get_lessons_for_category(category_id: int):
    """Fetches all lessons for a specific category ID."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, description FROM lessons WHERE category_id = %s ORDER BY id;", (category_id,))
        lessons = [{"id": row[0], "title": row[1], "description": row[2]} for row in cur.fetchall()]
        cur.close()
        return lessons
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn: conn.close()

@app.get("/api/v1/learning/phrases/{lesson_id}")
def get_phrases_for_lesson(lesson_id: int):
    """Fetches all phrases for a specific lesson ID."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT phrase_id_text, hindi_phrase, english_translation FROM phrases WHERE lesson_id = %s ORDER BY id;", (lesson_id,))
        phrases = [{"id": row[0], "hindi": row[1], "english": row[2]} for row in cur.fetchall()]
        cur.close()
        return phrases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn: conn.close()

@app.post("/api/v1/learning/evaluate")
async def evaluate_user_pronunciation(
        lang: str = Form(..., description="Language code (e.g., 'hi')"),
        phrase_id: str = Form(..., description="The text ID of the phrase (e.g., 'HIN_GREET_01')"),
        audio_file: UploadFile = File(..., description="User's audio recording.")
):
    """Handles pronunciation evaluation for the learning mode."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT hindi_phrase FROM phrases WHERE phrase_id_text = %s;", (phrase_id,))
        result = cur.fetchone()
        cur.close()
        if not result:
            raise HTTPException(status_code=404, detail=f"404: Phrase ID '{phrase_id}' not found.")
        target_phrase = result[0]

        contents = await audio_file.read()
        processed_audio = preprocess_audio(contents)
        transcribed_text = transcribe_audio_data(processed_audio, lang)

        if not transcribed_text:
            return {"transcription": "", "target_phrase": target_phrase, "score": 0, "feedback": "Could not hear you. Please speak louder."}

        evaluation = evaluate_pronunciation(transcribed_text, target_phrase, lang)
        return evaluation
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        if conn: conn.close()

# --- Part 2: Documenting Mode Endpoints ---

@app.post("/api/v1/dialects/contribute")
async def contribute_dialect(
    lang: str = Form(..., description="Language code (e.g., 'hi')"),
    user_spelling: str = Form(..., description="Contributor's spelling of the word."),
    meaning: str = Form(..., description="The meaning of the word."),
    region: str = Form(..., description="The region where the word is used."),
    notes: str = Form(None, description="Any additional context or notes."),
    audio_file: UploadFile = File(..., description="The audio recording.")
):
    """Handles user-submitted dialect contributions."""
    conn = None
    try:
        audio_bytes = await audio_file.read()
        processed_audio = preprocess_audio(audio_bytes)
        asr_transcription = transcribe_audio_data(processed_audio, lang)

        user_id = "user_abc_123" # Hardcoded for now

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

        is_rare = False
        check_query = "SELECT COUNT(*) FROM dialect_dictionary WHERE word = %s;"
        cur.execute(check_query, (asr_transcription,))
        count = cur.fetchone()[0]

        if count == 0:
            is_rare = True
            update_query = "UPDATE dialect_contributions SET status = %s WHERE id = %s;"
            cur.execute(update_query, ('pending_expert_validation', new_contribution_id))
            conn.commit()

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
        if conn: conn.close()





