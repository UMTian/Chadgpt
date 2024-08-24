from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
from io import BytesIO
import base64
from googletrans import Translator

# Load environment variables
load_dotenv()

# Configure API key for Gemini Pro
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Initialize pyttsx3 engine
engine = pyttsx3.init()

# Function to list and select available voices
def set_voice(engine, voice_name):
    voices = engine.getProperty('voices')
    for voice in voices:
        if voice_name.lower() in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break

# Set the desired voice (e.g., "Zira" for a female voice or "David" for a male voice on Windows)
desired_voice = "Zira"
set_voice(engine, desired_voice)

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
    try:
        st.write("Recognizing...")
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.write("Could not understand audio.")
        return ""
    except sr.RequestError as e:
        st.write(f"Could not request results: {e}")
        return ""

# Function to get Gemini response
def get_gemini_response(input):
    response = chat.send_message(input, stream=True)
    return response

# Function to generate audio from text using gTTS
def text_to_audio(text):
    tts = gTTS(text)
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# Function to play audio in Streamlit
def audio_player(audio_bytes, key):
    audio_base64 = base64.b64encode(audio_bytes.read()).decode()
    audio_html = f"""
    <audio controls>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Initialize Streamlit app
st.set_page_config(page_title="CHAD GPT", page_icon=":robot_face:")

st.title("CHAD GPT")
st.write("Welcome to CHAD GPT! Ask any question and get a response from the Gemini Pro model.")

# Initialize session state for chat history and speech if they don't exist
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Function to clear chat history
def clear_chat_history():
    st.session_state['chat_history'] = []
    st.experimental_rerun()

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
        audio_fp = text_to_audio(text)
        audio_player(audio_fp, key=f"audio_{len(st.session_state['chat_history'])}")

# Initialize the translator
translator = Translator()

# User input section at the bottom
st.subheader("Your Input")
with st.form(key='input_form'):
    input_type = st.selectbox("Input Type:", ["Text", "Voice"])
    if input_type == "Text":
        user_input = st.text_input("Enter your question here:", key="input")
    else:
        user_input = recognize_speech()
        if user_input == "":
            st.write("No audio input detected. Please try again.")
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
    st.experimental_rerun()  # Rerun the app to clear the input field
