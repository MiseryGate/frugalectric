import streamlit as st
import speech_recognition as sr

# Function to recognize speech from the microphone
def recognize_speech_from_mic():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Recognize speech using Google Web Speech API
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"

# Streamlit UI
st.title("Speech to Text Converter")
st.write("Press the button to start recording your speech.")

if st.button("Record Speech"):
    with st.spinner("Recording..."):
        text_output = recognize_speech_from_mic()
    st.success("Recording complete!")
    st.write("You said:", text_output)