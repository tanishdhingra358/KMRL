# ingest.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import pytesseract
from PIL import Image
import fitz  # PyMuPDF

# --- Configuration ---
PDF_DIRECTORY = "data"  # Create a folder named 'data' and put your PDFs there
CHROMA_DB_DIR = "chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# --- Tesseract OCR Function (from your Flask app) ---
def extract_text_with_ocr(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        doc.close()
    except: return text

def main():
    print("Starting document ingestion process...")
    
    # 1. Load documents
    documents = []
    for filename in os.listdir(PDF_DIRECTORY):
        if filename.endswith(".pdf"):
            filepath = os.path.join(PDF_DIRECTORY, filename)
            print(f"Processing {filepath}...")
            # Use our custom OCR extractor instead of PyPDFLoader for scanned docs
            text = extract_text_with_ocr(filepath)
            # Create a LangChain Document object
            from langchain.docstore.document import Document
            documents.append(Document(page_content=text, metadata={"source": filepath}))

    if not documents:
        print("No PDF documents found in the 'data' directory. Exiting.")
        return

    print(f"Loaded {len(documents)} documents.")

    # 2. Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} text chunks.")

    # 3. Create embeddings and store in ChromaDB
    print("Creating embeddings and saving to ChromaDB... (This may take a while)")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    # Create a new ChromaDB from the documents
    vector_store = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings, 
        persist_directory=CHROMA_DB_DIR
    )
    
    print("--- Ingestion Complete ---")
    print(f"Vector store created at: {CHROMA_DB_DIR}")

if __name__ == "__main__":
    main()