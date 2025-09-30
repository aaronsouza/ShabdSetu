import asyncio
import json
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client, handle_file
from typing import Dict, Tuple, List, Optional
from pathlib import Path
from datetime import datetime
import psycopg
import subprocess

# =================== DATABASE CREDENTIALS ===================
DB_HOST = "db.kgsxngrvzloaeyidprts.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "aaronashutosh2"

# =================== GRADIO CLIENT URLS ===================

TRANSLATION_APP_URL = "fischerman/en_indic_indictrans2_ai4bharat1"
TTS_APP_URL = "fischerman/indic-parler-tts"
ASR_APP_URL = "fischerman/Indic_ASR_Comparison_Multi"

# =================== Speaker Prompts ===================

SPEAKER_PROMPTS = {
    "Assamese": "Sita speaks in a calm voice", "Bengali": "Arjun speaks in a calm voice",
    "Bodo": "Maya speaks in a calm voice", "Chhattisgarhi": "Champa speaks in a calm voice",
    "Dogri": "Karan speaks in a calm voice", "Gujarati": "Yash speaks in a calm voice",
    "Hindi": "Rohit speaks in a calm voice", "Kannada": "Suresh speaks in a calm voice",
    "Malayalam": "Anjali speaks in a calm voice", "Manipuri": "Ranjit speaks in a calm voice",
    "Marathi": "Sunita speaks in a calm voice", "Nepali": "Amrita speaks in a calm voice",
    "Odia": "Manas speaks in a calm voice", "Punjabi": "Gurpreet speaks in a calm voice",
    "Sanskrit": "Aryan speaks in a calm voice", "Tamil": "Jaya speaks in a calm voice",
    "Telugu": "Lalitha speaks in a calm voice",
}

# =================== Global Variables ===================

translations_cache: Dict[Tuple[str, str], Dict[str, str]] = {}
CACHE_FILE = Path("translations_cache.json")

# Category Cache Variables
category_translations_cache: Dict[Tuple[str, str], str] = {}
CATEGORY_CACHE_FILE = Path("categories.json")

lessons_by_category = {
    "Greetings": ["Hello!", "Good morning!", "Good evening!", "Good night!", "Hi there!"],
    "Common Phrases": ["How are you?", "Please help me.", "Thank you.", "Excuse me.", "I don't understand."],
    "Travel": ["Where is the bus station?", "I need an auto.", "How much is the fare?",
               "I want to go to the airport.", "Can you show me the way?"],
    "Custom": []
}

TARGET_LANGUAGES = ["Hindi", "Marathi", "Kannada", "Tamil", "Telugu"]

translation_client = None
tts_client = None
asr_client = None


# =================== Database Helper Functions ===================

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection error.")


# =================== Helper Functions ===================

def save_cache_to_file():
    """Saves the main phrase translation cache."""
    try:
        with CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump({f"{k[0]}||{k[1]}": v for k, v in translations_cache.items()},
                      f, ensure_ascii=False, indent=2)
        print(f"Cache saved to {CACHE_FILE}")
    except IOError as e:
        print(f"Could not save cache to file: {e}")


def load_cache_from_file():
    """Loads the main phrase translation cache."""
    if not CACHE_FILE.exists():
        print("Cache file not found. Starting with an empty cache.")
        return
    try:
        with CACHE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            for k_str, v in data.items():
                parts = k_str.split("||")
                if len(parts) == 2:
                    translations_cache[(parts[0], parts[1])] = v
        print(f"Cache loaded from {CACHE_FILE}")
    except (IOError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading cache file: {e}. Starting with empty cache.")


def save_category_cache_to_file():
    """Saves the category name translation cache."""
    try:
        with CATEGORY_CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump(
                {f"{k[0]}||{k[1]}": v for k, v in category_translations_cache.items()},
                f, ensure_ascii=False, indent=2
            )
        print(f"Category cache saved to {CATEGORY_CACHE_FILE}")
    except IOError as e:
        print(f"Could not save category cache: {e}")


def load_category_cache_from_file():
    """Loads the category name translation cache."""
    if not CATEGORY_CACHE_FILE.exists():
        print("Category cache file not found. Starting with empty.")
        return
    try:
        with CATEGORY_CACHE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            for k_str, v in data.items():
                parts = k_str.split("||")
                if len(parts) == 2:
                    category_translations_cache[(parts[0], parts[1])] = v
        print(f"Category cache loaded from {CATEGORY_CACHE_FILE}")
    except (IOError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading category cache: {e}. Starting with empty.")


def get_speaker_description(language: str) -> str:
    return SPEAKER_PROMPTS.get(language, "A calm voice speaks the text.")


async def _get_tts_audio_async(translated_text: str, target_lang: str) -> Optional[str]:
    try:
        speaker_description = get_speaker_description(target_lang)
        result_filepath = await asyncio.to_thread(
            tts_client.predict,
            text=translated_text,
            description=speaker_description,
            api_name="/generate_finetuned"
        )
        if result_filepath and Path(result_filepath).exists():
            with Path(result_filepath).open("rb") as audio_file:
                audio_content = audio_file.read()
                return base64.b64encode(audio_content).decode('utf-8')
        return None
    except Exception as e:
        print(f"Failed TTS for '{translated_text}' in {target_lang}: {e}")
        return None


async def _get_and_cache_data_sequentially(input_text: str, target_lang: str) -> None:
    cache_key = (input_text, target_lang)
    cache_entry = translations_cache.get(cache_key)
    if cache_entry and 'text' in cache_entry and 'audio' in cache_entry:
        return
    if not cache_entry:
        cache_entry = {}

    # Translate text
    if 'text' not in cache_entry and translation_client:
        try:
            translation_text = await asyncio.to_thread(
                translation_client.predict,
                input_text=input_text,
                target_lang=target_lang,
                api_name="/translate_to_indic"
            )
            cache_entry['text'] = translation_text
        except Exception as e:
            print(f"Failed translation for '{input_text}' in {target_lang}: {e}")
            return

    # Generate TTS
    if 'audio' not in cache_entry and 'text' in cache_entry and tts_client:
        tts_audio_base64 = await _get_tts_audio_async(cache_entry['text'], target_lang)
        if tts_audio_base64:
            cache_entry['audio'] = tts_audio_base64

    if 'text' in cache_entry and 'audio' in cache_entry:
        translations_cache[cache_key] = cache_entry
        save_cache_to_file()


def _add_to_custom_category(phrase: str):
    if phrase not in lessons_by_category["Custom"]:
        lessons_by_category["Custom"].append(phrase)


async def translate_category_name(category_name: str, target_lang: str) -> str:
    cache_key = (category_name, target_lang)
    if cache_key in category_translations_cache:
        return category_translations_cache[cache_key]
    if not translation_client:
        return category_name
    try:
        translated_text = await asyncio.to_thread(
            translation_client.predict,
            input_text=category_name,
            target_lang=target_lang,
            api_name="/translate_to_indic"
        )
        category_translations_cache[cache_key] = translated_text
        save_category_cache_to_file()
        return translated_text
    except Exception as e:
        print(f"Failed to translate category '{category_name}' to {target_lang}: {e}")
        return category_name


# =================== FastAPI Setup ===================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global translation_client, tts_client, asr_client
    load_cache_from_file()
    load_category_cache_from_file()
    print("Starting Gradio clients and pre-caching...")
    try:
        translation_client = Client(TRANSLATION_APP_URL)
        tts_client = Client(TTS_APP_URL)
        asr_client = Client(ASR_APP_URL)
        print("Gradio clients loaded successfully.")
    except Exception as e:
        print(f"Error loading Gradio clients: {e}")
        translation_client = None
        tts_client = None
        asr_client = None

    if translation_client and tts_client:
        for target_lang in TARGET_LANGUAGES:
            for category, phrases in lessons_by_category.items():
                if category == "Custom":
                    continue
                for phrase in phrases:
                    await _get_and_cache_data_sequentially(phrase, target_lang)
            for category in lessons_by_category.keys():
                if category == "Custom":
                    continue
                await translate_category_name(category, target_lang)

    yield
    save_cache_to_file()
    save_category_cache_to_file()
    print("Application shutdown: Clients released.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Root")
def read_root():
    return {"message": "Welcome to the BGB client app! Go to /docs to use the translation API."}


# =================== Lessons Endpoint ===================

@app.get("/lessons/", summary="Get All Lessons")
async def get_lessons(target_lang: Optional[str] = None):
    if target_lang:
        translated_lessons_data = []
        category_tasks = []
        category_names = list(lessons_by_category.keys())
        for cat_name in category_names:
            category_tasks.append(translate_category_name(cat_name, target_lang))

        translated_names = await asyncio.gather(*category_tasks)

        for i, cat_name in enumerate(category_names):
            translated_lessons_data.append({
                "english_category": cat_name,
                "translated_category": translated_names[i],
                "phrases": lessons_by_category[cat_name]
            })

        return {"lessons_by_category": translated_lessons_data}

    return {"lessons_by_category": lessons_by_category}


# =================== Phrase Translation ===================

@app.get("/translate/lesson/{category_name}/{phrase_number}")
async def translate_text_by_lesson(category_name: str, phrase_number: int, target_lang: str):
    if category_name not in lessons_by_category:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found.")
    phrases = lessons_by_category[category_name]
    if not (0 <= phrase_number < len(phrases)):
        raise HTTPException(status_code=404, detail=f"Phrase number {phrase_number} not found.")
    input_text = phrases[phrase_number]
    await _get_and_cache_data_sequentially(input_text, target_lang)
    cache_entry = translations_cache.get((input_text, target_lang), {})
    return {
        "category": category_name,
        "english_sentence": input_text,
        "indic_sentence": cache_entry.get('text'),
        "indic_audio_base64": cache_entry.get('audio')
    }


@app.get("/translate/custom/")
async def translate_custom_phrase(phrase: str, target_lang: str):
    _add_to_custom_category(phrase)
    await _get_and_cache_data_sequentially(phrase, target_lang)
    cache_entry = translations_cache.get((phrase, target_lang), {})
    return {
        "category": "Custom",
        "english_sentence": phrase,
        "indic_sentence": cache_entry.get('text'),
        "indic_audio_base64": cache_entry.get('audio')
    }


# =================== Pronunciation Evaluation (FINAL FIX FOR ASR CRASH) ===================

@app.post("/evaluate/lesson/{category_name}/{phrase_number}/pronounce")
async def evaluate_lesson_phrase_pronunciation(
        category_name: str,
        phrase_number: int,
        target_lang: str = Query(..., description="Indic language being practiced."),
        audio_file: UploadFile = File(..., description="User audio recording (MP4/3GPP expected)."),
        selected_model: str = "IndicConformer"
):
    import subprocess  # Import subprocess for FFmpeg

    if asr_client is None:
        raise HTTPException(status_code=503, detail="ASR client not initialized.")
    if category_name not in lessons_by_category:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found.")
    phrases = lessons_by_category[category_name]
    if not (0 <= phrase_number < len(phrases)):
        raise HTTPException(status_code=404, detail=f"Phrase number {phrase_number} not found.")

    english_reference_text = phrases[phrase_number]
    await _get_and_cache_data_sequentially(english_reference_text, target_lang)
    cache_entry = translations_cache.get((english_reference_text, target_lang), {})
    indic_reference_text = cache_entry.get('text')

    if not indic_reference_text:
        raise HTTPException(status_code=500, detail=f"Missing translation for {target_lang}.")

    file_stem = Path(audio_file.filename).stem
    received_file_path = Path(f"temp_received_{file_stem}_input")
    wav_file_path = Path(f"temp_converted_{file_stem}.wav")

    try:
        # 1. Save the incoming audio file
        contents = await audio_file.read()
        await asyncio.to_thread(received_file_path.write_bytes, contents)

        # 2. CONVERSION STEP: Use FFmpeg to convert the received file to WAV
        subprocess.run(
            [
                "ffmpeg",
                "-i", str(received_file_path),  # Input file
                "-acodec", "pcm_s16le",  # Output codec: Uncompressed PCM
                "-ar", "16000",  # Sample rate: 16kHz (Standard for speech recognition)
                "-ac", "1",  # Channels: Mono
                str(wav_file_path)  # Output file: .wav
            ],
            check=True,  # Raise CalledProcessError if FFmpeg fails
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 3. Send the converted WAV file to the ASR client
        result = await asyncio.to_thread(
            asr_client.predict,
            audio_file=handle_file(str(wav_file_path)),  # Pass the converted WAV file
            selected_language=target_lang,
            selected_models=[selected_model],
            reference_text=indic_reference_text,
            api_name="/transcribe_audio"
        )

        # 4. Process ASR Result
        if not isinstance(result, tuple) or len(result) < 2 or not isinstance(result[1], dict):
            raise HTTPException(status_code=500, detail="Invalid response format from ASR model.")

        data_dict = result[1]

        # *** CRITICAL FIX: Check if the 'data' array exists and is NOT empty ***
        if not data_dict.get('data') or not data_dict['data'] or not data_dict['data'][0]:
            # Gracefully handle ASR failure (returning a 200 with 0.0 score and message)
            return {
                "language": target_lang,
                "english_reference": english_reference_text,
                "indic_reference": indic_reference_text,
                "user_transcription": "Could not transcribe audio.",
                "pronunciation_score": 0.0,
                "character_error_rate": 1.0,
                "word_error_rate": 1.0,
                "feedback": "We couldn't hear you clearly. Please try recording the phrase again!"
            }

        # Proceed only if data is safely available
        data_list = data_dict['data'][0]
        if len(data_list) < 6:
            raise HTTPException(status_code=500, detail="ASR model returned incomplete transcription data structure.")

        # Safely unpack the expected six elements
        _, transcription, wer_str, cer_str, _, _ = data_list

        try:
            cer = float(cer_str)
            wer = float(wer_str)
            weighted_error_rate = (0.85 * cer) + (0.15 * wer)
            pronunciation_score = round(max(0.0, 1.0 - weighted_error_rate), 4)

            if pronunciation_score >= 0.95:
                feedback = "Flawless! Excellent pronunciation. 🎉"
            elif pronunciation_score >= 0.85:
                feedback = "Great job! Very close to perfect."
            elif pronunciation_score >= 0.65:
                feedback = "Good attempt. Some key sounds need more practice."
            else:
                feedback = "Keep practicing! Review the original audio example for improvement."

            return {
                "language": target_lang,
                "english_reference": english_reference_text,
                "indic_reference": indic_reference_text,
                "user_transcription": transcription,
                "pronunciation_score": pronunciation_score,
                "character_error_rate": cer,
                "word_error_rate": wer,
                "feedback": feedback
            }
        except (ValueError, TypeError):
            raise HTTPException(status_code=500, detail="Failed to parse WER/CER from ASR model output.")
    except subprocess.CalledProcessError as e:
        # Handle conversion error
        print(f"FFmpeg conversion failed: {e.stderr.decode()}")
        raise HTTPException(status_code=500, detail=f"Audio processing failed (FFmpeg conversion error).")
    except Exception as e:
        print(f"Error during pronunciation evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        # 5. Cleanup both temporary files
        if received_file_path.exists():
            await asyncio.to_thread(received_file_path.unlink)
        if wav_file_path.exists():
            await asyncio.to_thread(wav_file_path.unlink)
