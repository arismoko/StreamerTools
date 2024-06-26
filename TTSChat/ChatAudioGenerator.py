from TTS.api import TTS
import os
import socket
import re

os.environ['COQUI_STT_MODEL_CACHE_CONFIRMATION'] = 'true'
print("Loading TTS model...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
print("TTS model loaded successfully!")

TWITCH_TOKEN = os.getenv('TWITCH_API_SECRET')  # Use the OAuth token you obtained
TWITCH_USERNAME = "ariasmoko"
CHANNEL = "#ariasmoko"
pathToSamples = "C:/Users/ari/XTTS-v2/samples/"
default_voice = "ariasmoko"

def connect_to_twitch():
    server = 'irc.chat.twitch.tv'
    port = 6667
    token = f"oauth:{TWITCH_TOKEN}"
    nickname = TWITCH_USERNAME
    channel = CHANNEL

    sock = socket.socket()
    sock.connect((server, port))
    sock.send(f"PASS {token}\r\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\r\n".encode('utf-8'))

    return sock

def digit_to_word(match):
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

def replace_digits_with_words(text):
    return re.sub(r'\d', digit_to_word, text)

def listen_for_messages(sock):
    while True:
        response = sock.recv(2048).decode('utf-8')
        if response.startswith('PING'):
            print("PING")
            sock.send("PONG\n".encode('utf-8'))
            print("PONG")
        print(response)
        user = parse_user(response)
        voice = default_voice  # Set default voice
        if user:
            # Check if user.wav exists in the samples folder
            user_voice_path = f"{pathToSamples}{user}.wav"
            if os.path.exists(user_voice_path):
                voice = user
            else:
                voice = "en_sample"
        message = parse_message(response)
        # Remove numbers from the message
        if message:
            message = replace_digits_with_words(message)
            message = re.sub(r'\d+', '', message)
            message = message[:300]  # Limit message length to 150 characters
            #if the message is empty, skip processing
            if re.match(r'^[\W_]+$', message) or message.strip() == "":
                continue
            print(f"Message: {message}")
            generate_chat_audio(message, voice)  # Pass the voice to the function

def generate(message, voice):
    tts.tts_to_file(text=message,
                    file_path="TTSCHAT/output.wav",
                    speaker_wav=f"{pathToSamples}{voice}.wav",
                    language="en")

def generate_chat_audio(message, voice):
    if not message:
        return  # Skip processing if no message is found
    generate(message, voice)

def parse_user(response):
    match = re.search(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', response)
    if match:
        return match.group(1)
    return None

def parse_message(response):
    match = re.search(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', response)
    if match:
        return match.group(3)
    return None

print("Connecting to Twitch...")
sock = connect_to_twitch()
print("Connected to Twitch")
listen_for_messages(sock)
