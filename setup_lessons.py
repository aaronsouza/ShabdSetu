import psycopg2
import os

# --- IMPORTANT: PASTE YOUR DATABASE CREDENTIALS HERE ---
DB_HOST = os.environ.get("DB_HOST", "db.biutmpyotmmsjcnbllff.supabase.co")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "aaronashutosh")
# ---

# --- The Complete Curriculum for BhashaBuddy ---
CURRICULUM = {
    "Greetings": {
        "description": "Learn the essential ways to greet people and introduce yourself.",
        "lessons": {
            "Formal Greetings": {
                "description": "Greetings for formal situations, elders, or professionals.",
                "phrases": [
                    ("HIN_GREET_01", "नमस्ते", "Hello / A respectful greeting"),
                    ("HIN_GREET_02", "आप कैसे हैं?", "How are you? (formal)"),
                    ("HIN_GREET_03", "मैं ठीक हूँ, धन्यवाद।", "I am fine, thank you."),
                    ("HIN_GREET_04", "आपसे मिलकर ख़ुशी हुई।", "Pleased to meet you."),
                ]
            },
            "Informal Greetings": {
                "description": "Casual greetings for friends and family.",
                "phrases": [
                    ("HIN_GREET_05", "और, क्या हाल है?", "So, what's up?"),
                    ("HIN_GREET_06", "सब बढ़िया।", "Everything is great."),
                    ("HIN_GREET_07", "फिर मिलते हैं।", "See you later."),
                ]
            }
        }
    },
    "Basic Grammar": {
        "description": "Understand the fundamental building blocks of Hindi sentences.",
        "lessons": {
            "Nouns and Pronouns": {
                "description": "Learn common nouns and how to refer to yourself and others.",
                "phrases": [
                    ("HIN_GRAMMAR_01", "यह एक किताब है।", "This is a book."),
                    ("HIN_GRAMMAR_02", "मेरा नाम आरव है।", "My name is Aarav."),
                    ("HIN_GRAMMAR_03", "वह मेरी दोस्त है।", "She is my friend."),
                ]
            }
        }
    },
    "Food & Dining": {
        "description": "Learn how to ask for things and order food at a restaurant.",
        "lessons": {
            "Ordering Food": {
                "description": "Essential phrases for eating out.",
                "phrases": [
                    ("HIN_FOOD_01", "एक पानी की बोतल, कृपया।", "One bottle of water, please."),
                    ("HIN_FOOD_02", "क्या आप यह फिर से बता सकते हैं?", "Can you repeat that?"),
                    ("HIN_FOOD_03", "बिल दीजिए।", "The bill, please."),
                ]
            }
        }
    }
}


def setup_lessons():
    """Connects to the database and populates it with the curriculum."""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        print("✅ Connection successful. Populating lessons...")

        for category_name, category_data in CURRICULUM.items():
            # Insert category and get its ID
            cur.execute(
                "INSERT INTO categories (name, description) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING RETURNING id;",
                (category_name, category_data['description']))
            result = cur.fetchone()
            if result is None:  # If category already existed, fetch its ID
                cur.execute("SELECT id FROM categories WHERE name = %s;", (category_name,))
                result = cur.fetchone()
            category_id = result[0]
            print(f"Processing Category: {category_name} (ID: {category_id})")

            for lesson_title, lesson_data in category_data['lessons'].items():
                # Insert lesson and get its ID
                cur.execute(
                    "INSERT INTO lessons (category_id, title, description) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING id;",
                    (category_id, lesson_title, lesson_data['description']))
                result = cur.fetchone()
                if result is None:
                    cur.execute("SELECT id FROM lessons WHERE title = %s;", (lesson_title,))
                    result = cur.fetchone()
                lesson_id = result[0]
                print(f"  -> Processing Lesson: {lesson_title} (ID: {lesson_id})")

                for phrase_id_text, hindi_phrase, english_translation in lesson_data['phrases']:
                    # Insert phrase
                    cur.execute(
                        "INSERT INTO phrases (lesson_id, phrase_id_text, hindi_phrase, english_translation) VALUES (%s, %s, %s, %s) ON CONFLICT (phrase_id_text) DO NOTHING;",
                        (lesson_id, phrase_id_text, hindi_phrase, english_translation))

        conn.commit()
        cur.close()
        print("\n✅✅✅ Database curriculum setup complete!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    setup_lessons()
