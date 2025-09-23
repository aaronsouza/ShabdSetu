from googletrans import Translator

# This dictionary maps our simple language codes to the codes required by Google Translate
LANG_CODE_MAP = {
    "hi": "hi", # Hindi
    "kn": "kn", # Kannada
    "ta": "ta"  # Tamil
    # You can add more languages here in the future
}

class TranslationService:
    """
    A service to handle translations using the Google Translate API.
    This is a lightweight and reliable alternative to local models.
    """
    def __init__(self):
        # The translator object is lightweight and can be created on the fly.
        self.translator = Translator()
        print("Google Translate Service: Ready.")

    def load_model(self):
        """
        Placeholder method. No model needs to be loaded for this service.
        This ensures compatibility with our existing setup_lessons.py script.
        """
        print("No local model to load. Using Google Translate API.")
        pass

    def translate(self, text: str, target_lang_code: str = "hi") -> str:
        """
        Translates a single string of English text to the target language.
        """
        if target_lang_code not in LANG_CODE_MAP:
            raise ValueError(f"Unsupported target language: {target_lang_code}")

        try:
            # Perform the translation using the library
            result = self.translator.translate(text, dest=LANG_CODE_MAP[target_lang_code])
            return result.text
        except Exception as e:
            print(f"❌ An error occurred during translation: {e}")
            return text # Return original text on failure

# Example of how to use this new service
if __name__ == '__main__':
    print("--- Running Google Translate Service Test ---")
    translator = TranslationService()

    english_text = "Hello, how are you?"
    hindi_translation = translator.translate(english_text, "hi")

    print(f"\nEnglish Original: '{english_text}'")
    print(f"Hindi Translation: '{hindi_translation}'")

    english_text_2 = "What do you recommend?"
    hindi_translation_2 = translator.translate(english_text_2, "hi")

    print(f"\nEnglish Original: '{english_text_2}'")
    print(f"Hindi Translation: '{hindi_translation_2}'")
    print("--- Test Complete ---")















