from TTS.api import TTS
import os
import re
import socket

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
        while True:
            response = sock.recv(2048).decode('utf-8')
            if self.handlePingResponse(sock, response):
                continue
            user = self.parse_user(response)
            # continue if user is nightbot or Nightbot
            if user == "nightbot" or user == "Nightbot":
                continue
            voice = self.getVoice(user)
            message = self.parse_message(response)
            self.handleMessage(message, voice)

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
            return  # Skip processing if no message is found
        self.generate(message, voice)

    def generate(self, message, voice):
        self.tts.tts_to_file(
            text=message,
            file_path="TTSCHAT/output.wav",
            speaker_wav=f"{self.pathToSamples}{voice}.wav",
            language="en"
        )

    def handleMessage(self, message, voice):
        if message:
            message = self.replace_digits_with_words(message)
            message = re.sub(r'\d+', '', message)
            # only read the message if its over 15 characters:
            if len(message) < 15 or voice == "Nightbot":
                return
            message = message[:150]  # Limit message length to 150 characters
            if re.match(r'^[\W_]+$', message) or message.strip() == "":
                return
            print(f"Message: {message}")
            self.generate_chat_audio(message, voice)

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
