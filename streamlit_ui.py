# streamlit_ui.py
import streamlit as st
import requests
import os

# --- Configuration ---
# This is the URL where your Flask backend is running
BACKEND_URL = "http://127.0.0.1:5000/analyze_document"

# --- Streamlit App UI ---
st.set_page_config(page_title="KMRL Document Analysis", layout="wide")
st.title("📄 KMRL Intelligent Document Hub")
st.write("Upload a scanned document (PDF) to automatically classify it and extract key information.")

# File uploader
uploaded_file = st.file_uploader("Choose a document to analyze...", type=['pdf', 'png', 'jpg', 'jpeg', 'docx'])

if uploaded_file is not None:
    st.info(f"File uploaded: {uploaded_file.name}")
    
    # Button to trigger analysis
    if st.button("Analyze Document"):
        with st.spinner("Processing document... This may take a moment."):
            try:
                # Prepare the file to be sent to the backend
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                # Send the request to the Flask backend API
                response = requests.post(BACKEND_URL, files=files)
                
                if response.status_code == 200:
                    # If successful, display the results
                    results = response.json()
                    st.success("Analysis Complete!")
                    
                    st.subheader("Document Category")
                    st.write(f"**{results.get('predicted_category', 'N/A')}**")
                    
                    st.subheader("Recommended Routing")
                    st.write(results.get('routing_action', 'N/A'))
                    
                    st.subheader("Extracted Action Items")
                    action_items = results.get('extracted_action_items', [])
                    if action_items:
                        for item in action_items:
                            st.write(f"- {item}")
                    else:
                        st.write("No action items found.")

                else:
                    # If the backend returns an error
                    st.error(f"An error occurred: {response.json().get('error', 'Unknown error')}")

            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Could not connect to the backend. Is the app.py server running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")