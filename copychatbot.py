import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from googletrans import Translator

# Load environment variables
load_dotenv()

# Configure API key for Gemini Pro
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Function to get Gemini response
def get_gemini_response(input_text):
    response = chat.send_message(input_text, stream=True)
    return response

# Initialize Streamlit app
st.set_page_config(page_title="CHAD GPT", page_icon=":robot_face:")

st.title("CHAD GPT")
st.write("Welcome to CHAD GPT! Ask any question and get a response from the Gemini Pro model.")

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Function to clear chat history
def clear_chat_history():
    st.session_state['chat_history'] = []

# Clear chat history button
if st.button("Clear Chat History"):
    clear_chat_history()

# Display chat history
st.subheader("Chat History")
for role, text in st.session_state['chat_history']:
    if role == "You":
        st.markdown(
            f"""
            <div style='background-color: #CCCCFF; padding: 10px; border-radius: 5px; margin-bottom: 5px; text-align: right;'>
                <b>{role}:</b> {text}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='background-color: #DCFEFF; padding: 10px; border-radius: 5px; margin-bottom: 5px; text-align: left;'>
                <b>{role}:</b> {text}
            </div>
            """,
            unsafe_allow_html=True
        )

# Initialize the translator
translator = Translator()

# User input section at the bottom
st.subheader("Your Input")
with st.form(key='input_form'):
    user_input = st.text_input("Enter your question here:", key="input")
    submit = st.form_submit_button("Ask")

if submit and user_input:
    # Detect and translate the input text to English
    detected_lang = translator.detect(user_input).lang
    if detected_lang != 'en':
        user_input_translated = translator.translate(user_input, src=detected_lang, dest='en').text
    else:
        user_input_translated = user_input

    response = get_gemini_response(user_input_translated)
    # Add user query and response to session state chat history
    st.session_state['chat_history'].append(("You", user_input))
    for chunk in response:
        # Translate the response back to the detected language if it was not English
        if detected_lang != 'en':
            response_translated = translator.translate(chunk.text, src='en', dest=detected_lang).text
        else:
            response_translated = chunk.text

        # Add both the translated and English responses to the chat history
        st.session_state['chat_history'].append(("Bot (English)", chunk.text))
        st.session_state['chat_history'].append(("Bot (Translated)", response_translated))

    # Simulate rerun by updating a dummy state variable
    st.session_state['rerun'] = st.session_state.get('rerun', 0) + 1
