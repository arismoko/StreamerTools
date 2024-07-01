# requires: RealTimeTTS
from functools import partial
from hashlib import md5
import json
from operator import mod
import os
import queue
import re
import socket
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from RealtimeTTS import TextToAudioStream, CoquiEngine


class TTSPlayer:
    def __init__(self, model: str) -> None:

        self.engine = CoquiEngine(
            model_name=model,
            comma_silence_duration=0.2,
            sentence_silence_duration=0.3,
            default_silence_duration=0.1,
            speed=1.2,
            voices_path="./samples/",
        )

        # these lines to find output device index list. select "default output"
        # import sounddevice as sd
        # print(sd.query_devices())
        self.stream = TextToAudioStream(self.engine, output_device_index=8)
        self.text_filters: List[Callable[[str], Optional[str]]] = []
        self.cur_voice = ""
        self.switch_voice("en_sample.wav")

    def add_filter(self, filter: Callable[[str], Optional[str]]):
        self.text_filters.append(filter)

    def play(self, text: str):
        for filter in self.text_filters:
            newtext = filter(text)
            if newtext is None:
                return
            text = newtext

        self.stream.feed(text)
        self.stream.play()

    def switch_voice(self, voice: Union[str, Path]):
        if self.cur_voice != str(voice):
            self.engine.set_voice(str(voice))
            self.cur_voice = voice


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


class ChatAudioGenerator:
    def __init__(self):
        print("Loading TTS model...")
        self.tts = TTSPlayer("tts_models/multilingual/multi-dataset/xtts_v2")
        self.tts.add_filter(bad_msg)
        self.tts.add_filter(Replacements())
        self.tts.add_filter(self.voice_filter)

        print("TTS model loaded successfully!")
        self.default_voice = "ariasmoko"
        self.TWITCH_TOKEN = os.getenv("TWITCH_API_SECRET")
        self.TWITCH_USERNAME = "ariasmoko"
        self.CHANNEL = "#ariasmoko"
        self.message_queue = queue.Queue()

    def voice_filter(self, txt: str) -> Optional[str]:
        if txt.startswith("!!"):
            txt = txt[2:]
            sample, msg = txt.split(" ", maxsplit=1)
            sample = f"{sample}.wav"
            samp = Path(self.tts.engine.voices_path) / sample  # type:ignore
            if samp.exists() and samp.is_file():
                self.tts.switch_voice(sample)
                return txt
            return None
        self.tts.switch_voice("en_sample.wav")
        return txt

    def connect_to_twitch(self):
        server = "irc.chat.twitch.tv"
        port = 6667
        token = f"oauth:{self.TWITCH_TOKEN}"
        nickname = self.TWITCH_USERNAME
        channel = self.CHANNEL

        sock = socket.socket()
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
