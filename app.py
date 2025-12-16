import streamlit as st
import requests
import json
import os 
import time


API_KEY = "AIzaXXXXXXXXXXXXXXXXXXXXXXX" 

# Check if the key is empty.
if not API_KEY:
    st.error("**API Key is missing.** Please insert your valid key directly into the app.py script.")
    st.stop()

# Configuration
MODEL = "gemini-2.5-flash" 

RAG_FILE_PATH = "syllabus_text.txt" 

# --- RAG KNOWLEDGE BASE SETUP (Chunking) ---
def load_syllabus_knowledge(file_path):
    """
    Loads the curriculum text and segments it into course-level chunks
    using 'Course Name' as a reliable delimiter.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        chunks = full_text.split("Course Name")
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                processed_chunks.append("Course Name" + chunk.strip())
            elif chunk.strip():
                processed_chunks.append(chunk.strip()) 
                    
        return processed_chunks
    except FileNotFoundError:
        st.error(f"Error: RAG knowledge file not found at {file_path}. Please ensure 'syllabus_text.txt' is in the same directory.")
        return None
    except Exception as e:
        st.error(f"Error reading RAG file: {e}")
        return None

# Load the curriculum text as a list of course chunks
CURRICULUM_CHUNKS = load_syllabus_knowledge(RAG_FILE_PATH)
if CURRICULUM_CHUNKS is None:
    st.stop() 
    
# --- RAG RETRIEVAL LOGIC ---
def retrieve_relevant_context(user_query, chunks, max_tokens=10000):
    """
    Performs basic keyword-based retrieval: finds the most relevant chunks 
    based on keywords in the query.
    """
    query_keywords = user_query.lower().split()
    relevant_chunks = []
    current_length = 0
    
    if chunks:
        overview_chunk = chunks[0]
        if len(overview_chunk) < max_tokens:
            relevant_chunks.append(overview_chunk)
            current_length += len(overview_chunk)

    for i, chunk in enumerate(chunks):
        if i == 0: continue 
        
        is_relevant = any(keyword in chunk.lower() for keyword in query_keywords if len(keyword) > 3)
        
        if is_relevant:
            if current_length + len(chunk) < max_tokens:
                relevant_chunks.append(chunk)
                current_length += len(chunk)
            else:
                 break
                 
    if not relevant_chunks:
        return ""
        
    return "\n\n--- NEXT RELEVANT COURSE ---\n\n".join(relevant_chunks)


# --- SYSTEM INSTRUCTION (CORE PERSONALIZATION) ---
SYSTEM_INSTRUCTION = (
    "You are an expert AI Assistant for the Bennett University School of AI (SOAI), positioned at the forefront of the 5th Industrial Generation of AI. "
    "Your tone must be highly academic, supportive, and focused on innovation, research, and application. "

    "***Crucial Institutional Details to use when appropriate:***\n"
    "1. **Dean:** Prof. (Dr.) Rajeev Tiwari. (Assistant Deans: Dr. Manoj Sharma & Dr. Pratyush Pranav).\n"
    "2. **Core Programs:** SOAI offers B.Tech, BCA, B.Sc., M.Tech, M.Sc., MCA, PG Diploma (AI in Healthcare in collaboration with MAX Healthcare), and Ph.D. programs in Artificial Intelligence.\n"
    "3. **Unique Strengths:** The curriculum is Cutting-Edge, NEP-Aligned, and co-developed with global tech leaders (NVIDIA, Microsoft, AWS). The school features strong industry integration (70-80% applied learning), and world-class research infrastructure including one of India's best NVIDIA AI Labs (DGX-1 V100).\n"
    
    "When answering questions, especially about applications, strongly connect the concepts to the School's "
    "key specialization areas (AgriTech, Digital Healthcare, FinTech, Robotics, LegalTech, Data Science) "
    "or emphasize the strong mathematical/scientific foundation and ethical implications, aligning with the School's philosophy. "
    "Ensure your responses are concise and structured using Markdown for excellent readability."
)

# --- SESSION STATE INITIALIZATION ---
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = -1 

# --- HELPER FUNCTIONS ---
def start_new_chat():
    st.session_state.current_chat_index = -1

def load_chat(index):
    st.session_state.current_chat_index = index

def get_current_messages():
    if st.session_state.current_chat_index == -1:
        return []
    return st.session_state.conversations[st.session_state.current_chat_index]["messages"]

def save_current_chat(title, new_message_history):
    if st.session_state.current_chat_index == -1:
        st.session_state.conversations.append({
            "title": title,
            "messages": new_message_history
        })
        st.session_state.current_chat_index = len(st.session_state.conversations) - 1
    else:
        st.session_state.conversations[st.session_state.current_chat_index]["messages"] = new_message_history


# --- 2. STREAMLIT UI SETUP ---
st.set_page_config(page_title="Bennett University AI Assistant", layout="wide")
st.title("AI.ra welcomes you - chatbot for SOAI BU")
st.caption("🚀 AI-powered expertise, aligned with BU's focus on research and interdisciplinary applications")

# --- SIDEBAR (OLD CHATS AND NEW CHAT BUTTON) ---
with st.sidebar:
    st.header("Chat History")
    
    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat()
        st.rerun() 

    st.markdown("---")
    
    if st.session_state.conversations:
        for i, conv in enumerate(st.session_state.conversations):
            if st.button(f"📄 {conv['title']}", key=f"chat_{i}", use_container_width=True):
                load_chat(i)
                st.rerun() 

# --- MAIN CHAT AREA ---

messages = get_current_messages()

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Ask a question to AI.ra..."):
    
    contents_for_api = []
    current_chat_history = messages + [{"role": "user", "content": user_prompt}]
    first_user_message = current_chat_history[0]
    
    RAG_CONTEXT = ""
    if st.session_state.current_chat_index == -1:
        RAG_CONTEXT = retrieve_relevant_context(user_prompt, CURRICULUM_CHUNKS)

    
    RAG_INJECTION = f"""
--- START OF SOAI CURRICULUM KNOWLEDGE BASE (Retrieved Relevant Context) ---
{RAG_CONTEXT}
--- END OF SOAI CURRICULUM KNOWLEDGE BASE ---
The user's subsequent questions relate to the content found in the knowledge base above. 
You are acting as the SOAI assistant and must use this retrieved document as the authoritative source 
for all course codes, book references, and specific subject details. DO NOT mention this knowledge base to the user.
"""
    for i, message in enumerate(current_chat_history):
        role = "model" if message["role"] == "assistant" else "user"
        message_content = message["content"]
        
        if i == 0 and message["role"] == "user":
             message_content = (
                 SYSTEM_INSTRUCTION + 
                 RAG_INJECTION +          
                 "\n\n--- USER QUESTION ---\n" + 
                 message_content
             )
        
        contents_for_api.append({
            "role": role, 
            "parts": [{"text": message_content}]
        })

    with st.chat_message("user"):
        st.markdown(user_prompt)
        
    # --- 3. API CALL LOGIC ---
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={API_KEY}"
    data = {"contents": contents_for_api}
    headers = {"Content-Type": "application/json"}
    
    with st.spinner("AI.ra is thinking..."):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(data))
            
            if res.status_code == 200:
                response_json = res.json()
                
                if response_json.get("candidates"):
                    out = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    
                    with st.chat_message("assistant"):
                        st.markdown(out)
                        
                    current_chat_history.append({"role": "assistant", "content": out})
                    
                    chat_title = " ".join(first_user_message['content'].split()[:5])
                    if not chat_title:
                        chat_title = f"New Chat {time.strftime('%H:%M:%S')}"

                    save_current_chat(chat_title, current_chat_history)
                else:
                    st.warning("AI.ra provided no response candidate. Try asking a different question.")

            else:
                # Display generic error for 400, 429, or any other API error
                error_message = res.json().get('error', {}).get('message', 'Unknown API error.')
                st.error(f"Error {res.status_code}: {error_message}. Please check your API key validity.")

        except requests.exceptions.RequestException as e:
            st.error(f"Network Error: Could not connect to the API. Details: {e}")