# setup_database.py
import psycopg2

# --- IMPORTANT: PASTE YOUR DATABASE CREDENTIALS HERE ---
DB_HOST = "db.biutmpyotmmsjcnbllff.supabase.co"  # e.g., "db.xxxxxxxx.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "aaronashutosh"
# ---

# This is the updated SQL code. It uses a DO block to safely create
# the custom type only if it doesn't already exist.
SQL_COMMANDS = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_enum') THEN
        CREATE TYPE status_enum AS ENUM ('pending_review', 'pending_expert_validation', 'verified', 'rejected');
    END IF;
END$$;

-- Table 1: The main, verified dictionary of dialect words
CREATE TABLE IF NOT EXISTS dialect_dictionary (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT,
    region TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 2: The table to store all incoming user contributions
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

-- Add one word to our main dictionary for testing the "rarity detector"
INSERT INTO dialect_dictionary (word, meaning, region)
VALUES ('नमस्ते', 'A respectful greeting', 'General Hindi')
ON CONFLICT (word) DO NOTHING;
"""

def setup_database():
    """Connects to the database and executes the setup commands."""
    conn = None
    try:
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        print("Connection successful. Creating tables...")
        cur.execute(SQL_COMMANDS)
        conn.commit()
        cur.close()
        print("✅ Database setup complete. Tables created and initial data inserted.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    setup_database()





