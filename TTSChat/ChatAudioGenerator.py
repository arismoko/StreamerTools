from TTS.api import TTS
import os
import socket
import re
import win32api
import win32con
import win32gui
import pygetwindow as gw
import win32gui
import time

os.environ['COQUI_STT_MODEL_CACHE_CONFIRMATION'] = 'true'
print("Loading TTS model...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
print("TTS model loaded successfully!")

TWITCH_TOKEN = os.getenv('TWITCH_API_SECRET')  # Use the OAuth token you obtained
TWITCH_USERNAME = "ariasmoko"
CHANNEL = "#ariasmoko"
pathToSamples = "C:/Users/ari/XTTS-v2/samples/"
default_voice = "ariasmoko"
twitchPlays = False
key_map = {
            'up': win32con.VK_UP,
            'u': win32con.VK_UP,
            'hold up': win32con.VK_UP,
            'hold u': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'hold down': win32con.VK_DOWN,
            'd': win32con.VK_DOWN,
            'hold d': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'hold left': win32con.VK_LEFT,
            'l': win32con.VK_LEFT,
            'hold l': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'hold right': win32con.VK_RIGHT,
            'r': win32con.VK_RIGHT,
            'hold r': win32con.VK_RIGHT,
            'a': 0x58,  # Virtual key code for 'X'
            'b': 0x5A,  # Virtual key code for 'Z'
            'y': 0x43,  # Virtual key code for 'C'
            'x': 0x56,  # Virtual key code for 'V'
            'lb': 0x51,  # Virtual key code for 'Q'
            'rb': 0x45,  # Virtual key code for 'E'
            'start': win32con.VK_RETURN,
            'select': win32con.VK_BACK
        }

windows = gw.getAllWindows()
snes9x_window = None
for win in windows:
    if "snes9x" in win.title.lower():
        print(f"Found Snes9x window: {win.title}")
        snes9x_window = win

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
        if handlePingResponse(sock, response):
            continue
        user = parse_user(response)
        voice = getVoice(user)
        message = parse_message(response)
        print(twitchPlays)
        process_twitch_plays_input(message)
        if isTwitchPlays(user, message) or twitchPlays:
            continue

        handleMessage(message, voice)

def getVoice(user):
    if user:
        user_voice_path = f"{pathToSamples}{user}.wav"
        if os.path.exists(user_voice_path):
            return user
        else:
            return "en_sample"
    return "en_sample"
def saveEmulator(user,message):
    if user == "ariasmoko" and message.strip().lower() == "!save-state":
        win32api.keybd_event(win32con.VK_F1,0,0,0)  # Key down
        win32api.keybd_event(win32con.VK_SHIFT,0,0,0)
        time.sleep(0.1)  # Small delay
        win32api.keybd_event(win32con.VK_F1,0,win32con.KEYEVENTF_KEYUP,0)  # Key up
        win32api.keybd_event(win32con.VK_SHIFT,0,win32con.KEYEVENTF_KEYUP,0)  # Key up
    
        print("State saved!")
        return True
def isTwitchPlays(user, message):
    if user == "ariasmoko" and message.strip().lower() == "!start-twitchplays":
        global twitchPlays
        twitchPlays = True
        print("Twitch Plays has started!")
        return True

def handleMessage(message, voice):
    if message:
        message = replace_digits_with_words(message)
        message = re.sub(r'\d+', '', message)
        message = message[:300]  # Limit message length to 150 characters
        # if the message is empty, skip processing
        if re.match(r'^[\W_]+$', message) or message.strip() == "":
            return
        print(f"Message: {message}")
        generate_chat_audio(message, voice)  # Pass the voice to the function

def handlePingResponse(sock, response):
    if response.startswith('PING'):
        sock.send("PONG\n".encode('utf-8'))
        print("WE PONGED THAT PING!")
        return True

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

def process_twitch_plays_input(command):
    if command is None or not twitchPlays:
        return None
    if snes9x_window.isActive:
        snes9x_window.activate()
    command = command.strip().lower()
    print(f"command in key_map: {command in key_map.keys()}")
    if command.strip().lower() in key_map.keys():
        vk_key = key_map[command]
        win32api.keybd_event(vk_key, 0, 0, 0)  # Key down
        pausetime = 0.05
        if 'hold' in command:
            pausetime = 1
        time.sleep(pausetime)  # Small delay
        win32api.keybd_event(vk_key, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up
    else:
        print(f"Key '{command}' not found in key map")


print("Connecting to Twitch...")
sock = connect_to_twitch()
print("Connected to Twitch")
listen_for_messages(sock)