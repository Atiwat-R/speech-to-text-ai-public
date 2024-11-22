# from IPython.display import display, HTML
# display(HTML("<style>.container { width:100% !important; }</style>"))

from __future__ import division
import asyncio
import json
import re
import sys
import os
import pyaudio
from google.oauth2 import service_account
from google.cloud import speech
from six.moves import queue
import time
from enum import Enum

from utils.translation import translate_text

from dotenv import load_dotenv
load_dotenv()

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# RATE = 44000
# CHUNK = int(RATE / 25)  # 100ms

STREAMING_LIMIT = 290000  # 290 seconds (to leave some buffer before the 305 seconds limit)
INACTIVITY_TIMEOUT = 5.0

SENTENCE_CHAR_LIMIT = 150

# Thai -> Eng
language= {
    "source_lang": "th-TH",
    "translated_lang": "en-US"
}

# # Eng -> Thai
# language= {
#     "source_lang": "en-US",
#     "translated_lang": "th-TH"
# }

GOOGLE_SERVICE_KEY = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_SHEET_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_SHEET_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_SHEET_PRIVATE_KEY"),
    "client_email": os.getenv("GOOGLE_SHEET_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_SHEET_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("GOOGLE_SHEET_CERT_URL"),
    "universe_domain": "googleapis.com"
}

profanities = []

with open('../profanities.json', 'r') as file:
    profanities = json.load(file)


class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

class TextColor(Enum):
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'  # Reset to default color

    @classmethod
    def create_colored_text(cls, text: str, color: 'TextColor') -> str:
        return f"{color.value}{text}{cls.RESET.value}"
    

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def filter_profanities(text, profanities):
    # Create a regular expression pattern to match any of the profanities
    profanity_pattern = re.compile('|'.join(map(re.escape, profanities)), re.IGNORECASE)
    
    # Function to replace the matched profanity with asterisks
    def replace_profanity(match):
        word = match.group()
        return '' * len(word)
    
    # Substitute the profanities in the text with asterisks
    filtered_text = profanity_pattern.sub(replace_profanity, text)

    return filtered_text

def listen_print_loop(responses):

    def log_records(transcript, transcript_confidence):
            logged = TextColor.create_colored_text(f"TEXT: - {transcript} -\nCONFIDENCE: - {transcript_confidence} -\n\n", TextColor.WHITE)
            print(logged, flush=True)

            # Append records in log file
            with open("../transcription/log.txt", "a") as file:
                file.write(strip_ansi_codes(logged))

    final_transcript = ""  # To accumulate the final output
    file_path = "../transcription/transcription.txt"  # Path to the output file
    file_path_translate = "../transcription/transcription_translate.txt"  # Path to the output file
    last_interim_time = time.time()

    for response in responses:
        if not response.results:
            continue
        
        result = response.results[0]
        if not result.alternatives:
            continue
        
        # Get the current transcript
        transcript = result.alternatives[0].transcript
        transcript_confidence = result.alternatives[0].confidence

        transcript = filter_profanities(transcript, profanities)

        current_time = time.time()



        final_transcript += f"{TextColor.create_colored_text(transcript, TextColor.GREEN)}"
        # print(final_transcript, flush=True)  # Print the accumulated final transcript

        # Translate into second language
        translation = asyncio.run(translate_text(strip_ansi_codes(final_transcript), target_language=language["translated_lang"], source_language=language["source_lang"]))
        translation = filter_profanities(translation, profanities)
        final_translation = TextColor.create_colored_text(translation, TextColor.YELLOW)

        print(f"NEW: {transcript}")
        print(f"FINAL: {final_transcript}")
        print(f"TRANSLATED: {final_translation}\n")

        if result.is_final:
            log_records(transcript=transcript, transcript_confidence=transcript_confidence)

        # Write the final transcript to the file, replacing the previous content
        with open(file_path, "w") as file:
            file.write(strip_ansi_codes(final_transcript))
        with open(file_path_translate, "w") as file:
            file.write(strip_ansi_codes(final_translation))

        final_transcript = ""
        last_interim_time = current_time

        if len(transcript) > SENTENCE_CHAR_LIMIT:
            log_records(transcript=transcript, transcript_confidence=transcript_confidence)
            break
    
        print("\n")
        

        # Check for inactivity
        if current_time - last_interim_time >= INACTIVITY_TIMEOUT:
            # Treat the current transcript as final
            if transcript.strip():
                final_transcript += f"{TextColor.create_colored_text(transcript, TextColor.GREEN)}\n"
                print(final_transcript, flush=True)
                
                with open(file_path, "w") as file:
                    file.write(strip_ansi_codes(final_transcript))

                final_transcript = ""
                last_interim_time = current_time



def main():

    google_speechtotext_apikey = service_account.Credentials.from_service_account_info(GOOGLE_SERVICE_KEY)
    client = speech.SpeechClient(credentials=google_speechtotext_apikey)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language["source_lang"],
        model='latest_long'
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True # True means it'll generate texts in more frequent shorter bursts
    )

    def start_streaming():
        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)
            listen_print_loop(responses)

    while True:
        print("Starting new stream...")
        start_time = time.time()
        try:
            start_streaming()
        except Exception as e:
            if e.code == 400:
                print(f". . .")
            else:
                print(f"Error during streaming: {e}")

        # If the stream duration limit is reached, restart the stream
        elapsed_time = time.time() - start_time
        if elapsed_time >= STREAMING_LIMIT / 1000:
            print(". . . . .")

if __name__ == "__main__":
    try:
        print()
        main()
    except KeyboardInterrupt:
        print()
        print("Stopping . . .")

