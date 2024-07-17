# requires: RealTimeTTS
import json
import os
import queue
import re
import socket
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union
from RealtimeTTS import TextToAudioStream, CoquiEngine
from dotenv import load_dotenv

load_dotenv()

URL_REGEX = re.compile(
    r"(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z0-9\u00a1-\uffff][a-z0-9\u00a1-\uffff_-]{0,62})?[a-z0-9\u00a1-\uffff}]\.)+(?:[a-z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?"
)


class TTSPlayer:
    def __init__(self, model: str):

        self.engine = CoquiEngine(
            model_name=model,
            voices_path="./samples/",
        )

        # these lines to find output device index list. select "default output"
        import sounddevice as sd

        print(sd.query_devices())
        self.stream = TextToAudioStream(self.engine, output_device_index=10)
        self.text_filters: List[Callable[[str], Optional[str]]] = []
        self.cur_voice = ""
        self.switch_voice("en_sample")

    def add_filter(self, filter: Callable[[str], Optional[str]]):
        self.text_filters.append(filter)

    def play(self, text: str):
        # add user as a parameter to load the voice for the user
        for filter in self.text_filters:
            newtext = filter(text)
            if newtext is None:
                return
            text = newtext

        self.stream.feed(text)
        self.stream.play()

    def switch_voice(self, voice: Union[str, Path]):
        # add user as a parameter to save the voice for the user
        # check if the user is in the user_voice.json file
        if self.cur_voice != str(voice):  # dont have to do this probs
            self.engine.set_voice(str(voice))  # move this to play?
            self.cur_voice = voice
            # update user voice / add user voice to the user_voice.json file

    # def save_user_voice(self, user: str, voice: str):

    # def load_user_voice(self, user: str):


class Replacements:
    def __init__(self) -> None:
        self.path = Path("replacements.json")
        self.last_modified = 0
        self.simple = []
        self.regex = []

    def check_reload(self):
        modified = self.path.stat().st_mtime
        if modified != self.last_modified:
            with open("replacements.json") as f:
                content = f.read()
                data: Dict[str, Dict[str, str]] = json.loads(content)
                self.simple = [i for i in data["simple"].items()]
                self.regex = [
                    (re.compile(rf"\b{r}\b"), w) for r, w in data["words"].items()
                ] + [(re.compile(r), w) for r, w in data["regex"].items()]

            self.last_modified = modified

    def __call__(self, txt: str) -> str:
        self.check_reload()
        for k, v in self.simple:
            txt = txt.replace(k, v)
        for rgx, v in self.regex:
            txt = rgx.sub(v, txt)
        return txt


def bad_msg(txt: str) -> Optional[str]:
    if re.match(r"^[\W_]+$", txt) or txt.strip() == "":
        return None
    return txt


def contains_url(txt: str) -> Optional[str]:
    match = URL_REGEX.search(txt)
    return txt if match is None else re.sub(URL_REGEX, "URL", txt)


class ChatAudioGenerator:
    def __init__(self):
        print("Loading TTS model...")
        self.tts = TTSPlayer("tts_models/multilingual/multi-dataset/xtts_v2")
        self.tts.add_filter(bad_msg)
        self.tts.add_filter(Replacements())
        self.tts.add_filter(self.voice_filter)
        self.tts.add_filter(contains_url)
        # send a test message to test the TTS
        print("TTS model loaded successfully!")
        self.default_voice = "en_sample"
        self.TWITCH_TOKEN = os.getenv("TWITCH_API_SECRET")
        print(f"Token is NONE? {self.TWITCH_TOKEN is None}")
        self.TWITCH_USERNAME = "ariasmoko"
        self.CHANNEL = "#ariasmoko"
        self.message_queue = queue.Queue()
        # check if user_voice.json exists and if not make it
        # if not Path("user_voice.json").exists():
        # with open("user_voice.json", "w") as f:
        # f.write(json.dumps({"default": self.default_voice}))

    def voice_filter(self, txt: str) -> Optional[str]:
        if txt.startswith("!"):
            txt = txt[1:]
            sample, msg = txt.split(" ", maxsplit=1)
            sample = f"{sample}"
            self.tts.switch_voice(sample)
            if msg:
                return msg
        return txt

    def connect_to_twitch(self):
        server = "irc.chat.twitch.tv"
        port = 6667
        token = f"oauth:{self.TWITCH_TOKEN}"
        nickname = self.TWITCH_USERNAME
        channel = self.CHANNEL

        sock = socket.socket();
        sock.connect((server, port))
        sock.send(f"PASS {token}\r\n".encode())
        sock.send(f"NICK {nickname}\r\n".encode())
        sock.send(f"JOIN {channel}\r\n".encode())

        return sock

    def listen_for_messages(self, sock: socket.socket):
        threading.Thread(target=self.process_messages).start()
        while True:
            response = sock.recv(2048).decode("utf-8")
            if self.handlePingResponse(sock, response):
                continue
            user = self.parse_user(response)
            if user == "nightbot" or user == "Nightbot":
                continue
            message = self.parse_message(response)
            if message:
                self.message_queue.put(message)

    def process_messages(self):
        while True:
            message = self.message_queue.get()
            audio_file_path = self.handle_message(message)
            if audio_file_path:
                return None

    def handle_message(self, message):
        if message:
            print(f"Message: {message}")
            return self.tts.play(message)
        return None

    def handlePingResponse(self, sock: socket.socket, response):
        if response.startswith("PING"):
            sock.send(b"PONG\n")
            print("WE PONGED THAT PING!")
            return True
        return False

    def parse_user(self, response) -> Optional[str]:
        match = re.search(
            r":(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)", response
        )
        if match:
            return match.group(1)
        return None

    def parse_message(self, response):
        match = re.search(
            r":(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)", response
        )
        if match:
            return match.group(3)
        return None

if __name__ == "__main__":
    chat_audio_generator = ChatAudioGenerator()
    print("Connecting to Twitch...")
    sock = chat_audio_generator.connect_to_twitch()
    print("Connected to Twitch")
    chat_audio_generator.listen_for_messages(sock)
