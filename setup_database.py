# setup_database.py
import psycopg2

# --- IMPORTANT: PASTE YOUR DATABASE CREDENTIALS HERE ---
DB_HOST = "db.biutmpyotmmsjcnbllff.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "aaronashutosh"
# ---

# This SQL script now sets up ALL tables for both Learning and Documenting modes.
SQL_COMMANDS = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_enum') THEN
        CREATE TYPE status_enum AS ENUM ('pending_review', 'pending_expert_validation', 'verified', 'rejected');
    END IF;
END$$;

-- Table for Learning Mode (Part 1)
CREATE TABLE IF NOT EXISTS phrases (
    id TEXT PRIMARY KEY, -- e.g., 'HIN_001'
    phrase TEXT NOT NULL,
    language_code CHAR(2) NOT NULL
);

-- Table for Documenting Mode - Dictionary (Part 2)
CREATE TABLE IF NOT EXISTS dialect_dictionary (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT,
    region TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for Documenting Mode - Contributions (Part 2)
CREATE TABLE IF NOT EXISTS dialect_contributions (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    audio_data BYTEA,
    user_spelling TEXT,
    asr_transcription TEXT,
    meaning TEXT,
    region TEXT,
    notes TEXT,
    status status_enum DEFAULT 'pending_review',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert initial data for the Learning Mode phrases
INSERT INTO phrases (id, phrase, language_code) VALUES
('HIN_001', 'नमस्ते आप कैसे हैं', 'hi'),
('HIN_002', 'मेरा नाम आरव है', 'hi'),
('HIN_003', 'नमस्ते', 'hi'),
('HIN_004', 'यह एक सुंदर दिन है', 'hi')
ON CONFLICT (id) DO NOTHING; -- Prevents errors if you run the script again

-- Insert initial data for the Documenting Mode dictionary
INSERT INTO dialect_dictionary (word, meaning, region)
VALUES ('नमस्ते', 'A respectful greeting', 'General Hindi')
ON CONFLICT (word) DO NOTHING;
"""

def setup_database():
    """Connects to the database and executes all setup commands."""
    conn = None
    try:
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        print("Connection successful. Setting up all tables...")
        cur.execute(SQL_COMMANDS)
        conn.commit()
        cur.close()
        print("✅ Database setup complete for all modes.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    setup_database()






