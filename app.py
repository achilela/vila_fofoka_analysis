import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv
import PyPDF2
from docx import Document
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Avatars
USER_AVATAR = "https://raw.githubusercontent.com/achilela/vila_fofoka_analysis/9904d9a0d445ab0488cf7395cb863cce7621d897/USER_AVATAR.png"
#BOT_AVATAR = "https://raw.githubusercontent.com/achilela/vila_fofoka_analysis/c4c5c8d8ead5831178cb213fc82a22f5cb8abae6/BOT_AVATAR.jpg"
BOT_AVATAR = "https://raw.githubusercontent.com/achilela/vila_fofoka_analysis/991f4c6e4e1dc7a8e24876ca5aae5228bcdb4dba/Ataliba_Avatar.jpg"

# Preconfigured bio response
ATALIBA_BIO = """
**I am Ataliba Miguel's Digital Twin** 🤖

**Background:**
- 🎓 Mechanical Engineering (BSc)
- ⛽ Oil & Gas Engineering (MSc Specialization)
- 🔧 17+ years in Oil & Gas Industry
- 🔍 Current: Topside Inspection Methods Engineer @ TotalEnergies
- 🤖 AI Practitioner Specialist
- 🚀 Founder of ValonyLabs (AI solutions for industrial corrosion, retail analytics, and KPI monitoring)

**Capabilities:**
- Technical document analysis
- Engineering insights
- AI-powered problem solving
- Cross-domain knowledge integration

Ask me about engineering challenges, AI applications, or industry best practices!
"""

# Configure UI
st.markdown("""
    <style>
    @import url('https://fonts.cdnfonts.com/css/tw-cen-mt');
    * { font-family: 'Tw Cen MT', sans-serif; }
    .st-emotion-cache-1y4p8pa { padding: 2rem 1rem; }
    </style>
    """, unsafe_allow_html=True)
st.title("🚀 Ataliba o Agent Nerdx")

# File upload in sidebar
with st.sidebar:
    st.header("📁 Document Hub")
    uploaded_file = st.file_uploader("Upload technical documents", type=["pdf", "docx", "xlsx", "xlsm"])

# Session state initialization
if "file_context" not in st.session_state:
    st.session_state.file_context = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def parse_file(file):
    """Process uploaded file and return text content"""
    try:
        if file.type == "application/pdf":
            reader = PyPDF2.PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
            df = pd.read_excel(file)
            return df.to_string()
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

# Process file upload
if uploaded_file and not st.session_state.file_context:
    st.session_state.file_context = parse_file(uploaded_file)
    if st.session_state.file_context:
        st.sidebar.success("✅ Document loaded successfully")

def generate_response(prompt):
    """Generate AI response with bio fallback"""
    # Check for Ataliba-related questions
    bio_triggers = [
        'who are you', 'ataliba', 'yourself', 'skilled at', 
        'background', 'experience', 'valonylabs', 'totalenergies'
    ]
    
    if any(trigger in prompt.lower() for trigger in bio_triggers):
        for line in ATALIBA_BIO.split('\n'):
            yield line + '\n'
            time.sleep(0.1)
        return

    try:
        messages = [{
            "role": "system",
            "content": f"Expert technical assistant. Current document:\n{st.session_state.file_context}"
        } if st.session_state.file_context else {
            "role": "system",
            "content": "Expert technical assistant. Be concise and professional."
        }]
        
        messages.append({"role": "user", "content": prompt})
        
        start = time.time()
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-beta",
                "messages": messages,
                "temperature": 0.2,
                "stream": True
            },
            stream=True
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = line.decode('utf-8').replace('data: ', '')
                if chunk == '[DONE]': break
                try:
                    data = json.loads(chunk)
                    delta = data['choices'][0]['delta'].get('content', '')
                    full_response += delta
                    yield delta
                except:
                    continue
        
        # Performance metrics
        tokens = len(full_response.split())
        yield f"\n\n⚡ {tokens} tokens | 🕒 {tokens/(time.time()-start):.1f}t/s | 💰 ${tokens*0.00002:.4f}"
        
    except Exception as e:
        yield f"⚠️ API Error: {str(e)}"

# Chat interface
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar=USER_AVATAR if msg["role"] == "user" else BOT_AVATAR):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about documents or technical matters..."):
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in generate_response(prompt):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
