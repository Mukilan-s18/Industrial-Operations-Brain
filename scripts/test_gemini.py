"""Standalone Gemini API test -- tries newer models with potentially separate quotas."""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print(f"[OK] API key loaded (starts with: {api_key[:10]}...)")

models_to_try = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

for model_name in models_to_try:
    print(f"\n[...] Trying model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello from Gemini!' and nothing else.")
        print(f"[OK] {model_name} responded: {response.text}")
        print(f"\n[SUCCESS] API key works! Working model: {model_name}")
        break
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"[WARN] {model_name}: Quota exhausted, trying next...")
        else:
            print(f"[ERROR] {model_name}: {error_msg[:300]}")
else:
    print("\n[FAIL] All models have exhausted their quota.")
    print("You may need to wait for quota reset or enable billing.")
