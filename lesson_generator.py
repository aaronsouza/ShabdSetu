import torch

# -----------------
# 1. DATABASE & CACHING
# -----------------

# English-only master database for all lesson content - to be upscaled later with larger database
MASTER_LESSON_DB = [
    {
        "lesson_id": "EN_L1",
        "lesson_title": "Lesson 1: Basic Greetings",
        "phrases": [
            {"phrase_id": "EN_P101", "text": "Hello, how are you?"},
            {"phrase_id": "EN_P102", "text": "My name is BhashaBuddy."},
            {"phrase_id": "EN_P103", "text": "Hello"},
        ]
    },
    {
        "lesson_id": "EN_L2",
        "lesson_title": "Lesson 2: Common Questions",
        "phrases": [{"phrase_id": "EN_P201", "text": "What is your name?"}]
    }
]

# -----------------
# 2. TRANSLATION LOGIC
# -----------------

def translate_text(text: str, dest_lang: str, model, tokenizer, device, lang_codes, cache) -> str:
    """Translates text using the loaded AI4Bharat model and a cache."""
    if dest_lang == 'en' or model is None:
        return text
    model_lang_code = lang_codes.get(dest_lang)
    if not model_lang_code:
        return text
    cache_key = (text, dest_lang)
    if cache_key in cache:
        return cache[cache_key]
    try:
        input_text = f"<{model_lang_code}> {text}"
        inputs = tokenizer(input_text, return_tensors="pt", padding=True).to(device)
        generated_ids = model.generate(**inputs, max_length=128, num_beams=5)
        result = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        cache[cache_key] = result
        return result
    except Exception as e:
        print(f"AI4Bharat translation error: {e}")
        return text

# -----------------
# 3. LESSON & PHRASE HELPERS
# -----------------

def get_phrase_by_id(phrase_id: str) -> str | None:
    """Helper to find the original English text for a phrase_id."""
    for lesson in MASTER_LESSON_DB:
        for phrase in lesson["phrases"]:
            if phrase["phrase_id"] == phrase_id:
                return phrase["text"]
    return None

def get_translated_phrase(phrase_id: str, lang: str, model, tokenizer, device, lang_codes, cache) -> str | None:
    """Finds a phrase by ID and translates it to the target language."""
    english_text = get_phrase_by_id(phrase_id)
    if not english_text:
        return None
    return translate_text(english_text, lang, model, tokenizer, device, lang_codes, cache)

def generate_lessons_for_language(lang: str, model, tokenizer, device, lang_codes, cache):
    """Generates the full lesson list for a language by translating the master DB."""
    translated_lessons = []
    for lesson in MASTER_LESSON_DB:
        translated_title = translate_text(lesson["lesson_title"], lang, model, tokenizer, device, lang_codes, cache)
        translated_phrases = []
        for phrase in lesson["phrases"]:
            translated_phrases.append({
                "phrase_id": phrase["phrase_id"],
                "text": translate_text(phrase["text"], lang, model, tokenizer, device, lang_codes, cache),
                "translation_en": phrase["text"]
            })
        translated_lessons.append({
            "lesson_id": lesson["lesson_id"],
            "lesson_title": translated_title,
            "lesson_title_en": lesson["lesson_title"], # <-- THIS LINE IS NEW
            "phrases": translated_phrases
        })
    return {"lessons": translated_lessons}

