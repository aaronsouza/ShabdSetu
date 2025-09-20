# pronunciation_evaluator.py (Simplified Version)

import jellyfish

# This is our new, simple phoneme converter. It has NO external dependencies.
# It's not perfect, but it's good enough and it will work on your system.
HINDI_PHONEME_MAP = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ः': 'h', '्': ''
}

def simple_text_to_phonemes(text: str) -> list:
    """
    Converts Hindi text to a list of phonemes using our simple dictionary.
    """
    phonemes = []
    for char in text.replace(" ", ""):
        if char in HINDI_PHONEME_MAP:
            sound = HINDI_PHONEME_MAP[char]
            if sound:
                phonemes.append(sound)
    return phonemes

def calculate_accuracy_score(transcribed_text: str, target_text: str) -> float:
    if not transcribed_text or not target_text:
        return 0.0
    distance = jellyfish.levenshtein_distance(transcribed_text, target_text)
    max_len = max(len(transcribed_text), len(target_text))
    similarity = (max_len - distance) / max_len
    return max(0, similarity * 100)

def find_phoneme_errors(transcribed_phonemes: list, target_phonemes: list) -> list:
    errors = []
    for i, (target_ph, transcribed_ph) in enumerate(zip(target_phonemes, transcribed_phonemes)):
        if target_ph != transcribed_ph:
            error_message = f"Check your '{target_ph}' sound, you pronounced it more like '{transcribed_ph}'."
            errors.append(error_message)
            if len(errors) >= 2:
                break
    return errors

def evaluate_pronunciation(transcribed_text: str, target_text: str, lang: str):
    word_accuracy = calculate_accuracy_score(transcribed_text, target_text)

    # We only support Hindi for phonemes with this simple method
    if lang == 'hi':
        transcribed_phonemes = simple_text_to_phonemes(transcribed_text)
        target_phonemes = simple_text_to_phonemes(target_text)
        phoneme_accuracy = calculate_accuracy_score(" ".join(transcribed_phonemes), " ".join(target_phonemes))
    else:
        transcribed_phonemes = []
        target_phonemes = []
        phoneme_accuracy = word_accuracy # Fallback if not Hindi

    final_score = (word_accuracy * 0.3) + (phoneme_accuracy * 0.7)
    final_score = round(final_score, 2)

    feedback_messages = []
    if final_score >= 95:
        feedback_messages.append("Excellent pronunciation! Perfect job.")
    elif final_score >= 80:
        feedback_messages.append("Great job! Almost perfect.")
    else:
        phoneme_errors = find_phoneme_errors(transcribed_phonemes, target_phonemes)
        if phoneme_errors:
            feedback_messages.extend(phoneme_errors)
        else:
            feedback_messages.append("Good attempt! Keep practicing.")

    return {
        "transcription": transcribed_text,
        "target_phrase": target_text,
        "score": final_score,
        "feedback": " ".join(feedback_messages),
        "details": {
            "transcribed_phonemes": transcribed_phonemes,
            "target_phonemes": target_phonemes,
        }
    }


