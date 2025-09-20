import io
import torch
import numpy as np
import noisereduce as nr
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Wav2Vec2ForCTC,
    Wav2Vec2Processor
)
from pydub import AudioSegment
from pronunciation_evaluator import evaluate_pronunciation
from lesson_generator import generate_lessons_for_language, get_translated_phrase

# --- App Initialization ---
app = FastAPI(
    title="Bhasha Buddy API",
    description="Unified API for serving language lessons and evaluating pronunciation.",
    version="5.0.0"
)

# --- Global Variables ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TRANSLATION_MODEL = None
TRANSLATION_TOKENIZER = None
ASR_MODELS = {}
translation_cache = {}

#--related to the baloo font codes for multilingual support
AI4BHARAT_LANG_CODES = {
    "hi": "hin_Deva", "mr": "mar_Deva", "gu": "guj_Gujr", "bn": "ben_Beng",
    "pa": "pan_Guru", "ta": "tam_Taml", "te": "tel_Telu", "kn": "kan_Knda",
    "ml": "mal_Mlym"
}


# --- Model Loading on Startup ---
@app.on_event("startup")
async def load_models():
    global TRANSLATION_MODEL, TRANSLATION_TOKENIZER

    # Load Translation Model
    trans_model_name = "ai4bharat/indictrans2-en-indic-dist-200M"
    print(f"Loading Translation model on device: {DEVICE}...")
    try:
        TRANSLATION_TOKENIZER = AutoTokenizer.from_pretrained(trans_model_name, trust_remote_code=True)
        TRANSLATION_MODEL = AutoModelForSeq2SeqLM.from_pretrained(trans_model_name, trust_remote_code=True).to(DEVICE)
        print("✅ Translation model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading Translation model: {e}")

    # Load ASR Model
    print("Loading ASR models...")
    asr_model_name = "ai4bharat/indicwav2vec-hindi"
    try:
        processor = Wav2Vec2Processor.from_pretrained(asr_model_name)
        model = Wav2Vec2ForCTC.from_pretrained(asr_model_name)
        ASR_MODELS["hi"] = {"processor": processor, "model": model}
        print(f"✅ Successfully loaded ASR model for Hindi")
    except Exception as e:
        print(f"❌ Error loading ASR model for Hindi: {e}")


# --- Audio Processing ---
def preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio_segment = audio_segment.set_channels(1).set_frame_rate(target_sr)
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32768.0
        return nr.reduce_noise(y=samples, sr=target_sr, prop_decrease=0.8)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")


def transcribe_audio_data(audio_data: np.ndarray, lang: str) -> str:
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


# --- API Endpoints ---
@app.get("/api/v1/lessons/{lang}")
def get_lessons(lang: str):
    return generate_lessons_for_language(
        lang, TRANSLATION_MODEL, TRANSLATION_TOKENIZER, DEVICE,
        AI4BHARAT_LANG_CODES, translation_cache
    )


@app.post("/api/v1/learning/evaluate")
async def evaluate_user_pronunciation(
        lang: str = Form(...),
        phrase_id: str = Form(...),
        audio_file: UploadFile = File(...)
):
    target_phrase = get_translated_phrase(
        phrase_id, lang, TRANSLATION_MODEL, TRANSLATION_TOKENIZER, DEVICE,
        AI4BHARAT_LANG_CODES, translation_cache
    )
    if not target_phrase:
        raise HTTPException(status_code=404, detail=f"Phrase ID '{phrase_id}' not found.")

    contents = await audio_file.read()
    processed_audio = preprocess_audio(contents)
    transcribed_text = transcribe_audio_data(processed_audio, lang)

    if not transcribed_text:
        return {
            "transcription": "", "target_phrase": target_phrase, "score": 0,
            "feedback": "We couldn't hear you clearly. Please try speaking louder."
        }

    evaluation = evaluate_pronunciation(transcribed_text, target_phrase, lang)
    return evaluation


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Bhasha Buddy API!"}