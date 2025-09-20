# test_download.py
import os

# --- IMPORTANT ---
# PASTE YOUR HUGGING FACE TOKEN HERE
HF_TOKEN = "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"
# ---

# Set the token as an environment variable for the library to use
os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN

from transformers import Wav2Vec2ForCTC

MODEL_NAME = "./indicwav2vec-hindi"

print(f"Attempting to download model: {MODEL_NAME}")
print("This might take a moment...")

try:
    # We will try to download just one model and see the result.
    # The `use_auth_token` is the old name for `token`, but is good for testing.
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)
    print("\n✅ SUCCESS! The model was downloaded successfully.")
    print("This means your network connection is now working.")

except Exception as e:
    print("\n❌ FAILED: The download failed.")
    print("This is the real underlying error message:")
    print("---------------------------------------------")
    # This will print the detailed error, which is what we need.
    print(e)
    print("---------------------------------------------")