# check_setup.py
import os
from dotenv import load_dotenv

print("--- 🛠 Checking Project Setup ---")

# 1. Check for .env file and API key
try:
    if load_dotenv():
        print("✅ .env file loaded successfully.")
        if os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY"):
            print("✅ API Key found in environment.")
        else:
            print("⚠ WARNING: .env file found, but no GOOGLE_API_KEY or OPENAI_API_KEY variable was found inside.")
    else:
        print("❌ ERROR: .env file not found. Please create it and add your API key.")
except Exception as e:
    print(f"❌ ERROR loading .env file: {e}")

# 2. Check for critical libraries
try:
    import streamlit
    import langchain
    import chromadb
    print("✅ Core libraries (Streamlit, LangChain, ChromaDB) are installed.")
except ImportError as e:
    print(f"❌ ERROR: A critical library is missing: {e}. Please run 'pip install -r requirements.txt'.")

# 3. Check for documents folder
if os.path.isdir("documents"):
    print("✅ 'documents' folder exists.")
else:
    print("⚠ WARNING: 'documents' folder not found. Please create it and add your sample files.")

print("\n--- ✅ Setup Check Complete ---")
print("If all checks are green, you are ready for Step 1!")