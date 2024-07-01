from TTS.api import TTS
import os
import re
import socket
import queue
import threading
import time
import wave

class ChatAudioGenerator:
    def __init__(self):
        os.environ['COQUI_STT_MODEL_CACHE_CONFIRMATION'] = 'true'
        print("Loading TTS model...")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        print("TTS model loaded successfully!")
        self.pathToSamples = "C:/Users/ari/XTTS-v2/samples/"
        self.default_voice = "ariasmoko"
        self.TWITCH_TOKEN = os.getenv('TWITCH_API_SECRET')
        self.TWITCH_USERNAME = "ariasmoko"
        self.CHANNEL = "#ariasmoko"
        self.message_queue = queue.Queue()

    def connect_to_twitch(self):
        server = 'irc.chat.twitch.tv'
        port = 6667
        token = f"oauth:{self.TWITCH_TOKEN}"
        nickname = self.TWITCH_USERNAME
        channel = self.CHANNEL

        sock = socket.socket()
        sock.connect((server, port))
        sock.send(f"PASS {token}\r\n".encode('utf-8'))
        sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
        sock.send(f"JOIN {channel}\r\n".encode('utf-8'))

        return sock

    def listen_for_messages(self, sock):
        threading.Thread(target=self.process_messages).start()
        while True:
            response = sock.recv(2048).decode('utf-8')
            if self.handlePingResponse(sock, response):
                continue
            user = self.parse_user(response)
            if user == "nightbot" or user == "Nightbot":
                continue
            voice = self.getVoice(user)
            message = self.parse_message(response)
            if message:
                self.message_queue.put((message, voice))

    def process_messages(self):
        while True:
            message, voice = self.message_queue.get()
            audio_file_path = self.handleMessage(message, voice)
            if audio_file_path:
                audio_duration = self.get_audio_duration(audio_file_path)
                time.sleep(audio_duration +.5)

    def get_audio_duration(self, file_path):
        with wave.open(file_path, 'rb') as audio_file:
            frames = audio_file.getnframes()
            rate = audio_file.getframerate()
            duration = frames / float(rate)
        return duration

    def digit_to_word(self, match):
        digit_map = {
            '0': 'zero',
            '1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine'
        }
        return digit_map[match.group(0)]

    def replace_digits_with_words(self, text):
        return re.sub(r'\d', self.digit_to_word, text)

    def generate_chat_audio(self, message, voice):
        if not message:
            return None
        return self.generate(message, voice)

    def generate(self, message, voice):
        file_path = "output.wav"
        self.tts.tts_to_file(
            text=message,
            file_path=file_path,
            speaker_wav=f"{self.pathToSamples}{voice}.wav",
            language="en"
        )
        return file_path

    def handleMessage(self, message, voice):
        if message:
            message = self.replace_digits_with_words(message)
            message = re.sub(r'\d+', '', message)
            if len(message) < 15 or voice == "Nightbot":
                return None
            message = message[:250]
            if re.match(r'^[\W_]+$', message) or message.strip() == "":
                return None
            print(f"Message: {message}")
            return self.generate_chat_audio(message, voice)
        return None

    def getVoice(self, user):
        if user:
            user_voice_path = f"{self.pathToSamples}{user}.wav"
            if os.path.exists(user_voice_path):
                return user
            else:
                return "en_sample"
        return "en_sample"

    def handlePingResponse(self, sock, response):
        if response.startswith('PING'):
            sock.send("PONG\n".encode('utf-8'))
            print("WE PONGED THAT PING!")
            return True
        return False

    def parse_user(self, response):
        match = re.search(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', response)
        if match:
            return match.group(1)
        return None

    def parse_message(self, response):
        match = re.search(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', response)
        if match:
            return match.group(3)
        return None

if __name__ == "__main__":
    chat_audio_generator = ChatAudioGenerator()
    print("Connecting to Twitch...")
    sock = chat_audio_generator.connect_to_twitch()
    print("Connected to Twitch")
    chat_audio_generator.listen_for_messages(sock)
