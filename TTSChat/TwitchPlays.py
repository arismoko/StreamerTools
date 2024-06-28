import os
import socket
import re
import win32api
import win32con
import pygetwindow as gw
import time
import pyvjoy
import json
import shutil
from datetime import datetime
import asyncio
import concurrent.futures

class TwitchPlays:
    def __init__(self):
        self.TWITCH_TOKEN = os.getenv('TWITCH_API_SECRET')
        self.TWITCH_USERNAME = "ariasmoko"
        self.CHANNEL = "#ariasmoko"
        self.key_map = {
            'up': win32con.VK_UP,
            'u': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'd': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'l': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'r': win32con.VK_RIGHT,
            'a': 0x58,
            'b': 0x5A,
            'y': 0x43,
            'x': 0x56,
            'lb': 0x51,
            'rb': 0x45,
            'start': win32con.VK_RETURN,
            'select': win32con.VK_BACK
        }
        
        self.controller_map = {
            'u': 'axis_y_minus', 'd': 'axis_y_plus', 'l': 'axis_x_minus', 'r': 'axis_x_plus',  # left stick short
            'du': 13, 'dd': 14, 'dl': 15, 'dr': 16,  # D-Pad Short using integers
            'move-u': 'axis_y_minus', 'move-d': 'axis_y_plus', 'move-l': 'axis_x_minus', 'move-r': 'axis_x_plus', # left stick long
            'dpad-u': 13, 'dpad-d': 14, 'dpad-l': 15, 'dpad-r': 16,  # D-Pad Long using integers
            'll': 'axis_ry_minus', 'lr': 'axis_ry_plus', 'lu': 'axis_rx_minus', 'ld': 'axis_rx_plus',  # right stick short
            'look-u': 'axis_ry_minus', 'look-d': 'axis_ry_plus', 'look-l': 'axis_rx_minus', 'look-r': 'axis_rx_plus',  # Right Stick
            'a': 1, 'b': 2, 'x': 3, 'y': 4,  # Buttons using integers
            'lb': 5, 'rb': 6, 'start': 7, 'select': 8,  # Shoulder Buttons and Start/Select using integers
            'l3': 9, 'r3': 10, 'rt': 11, 'lt': 12  # L3, R3, RT, LT using integers
        }

        self.program_name = input("What is the name of the program/the name we should look for inside of the title of the window Twitch chat is controlling? ").strip().lower()
        self.target_window = None
        self.find_target_window()

        self.use_gamepad = input("Would you like to send Xbox controller input instead? (Y/N): ").strip().lower() == 'y'
        if self.use_gamepad:
            self.j = pyvjoy.VJoyDevice(1)
        print("Connecting to Twitch...")
        self.sock = self.connect_to_twitch()
        print("Connected to Twitch")
        
        self.save_folder_info = self.check_save_folder()
        
    def check_save_folder(self):
        use_save_folder = input("Would you like to use a save folder? (Y/N): ").strip().lower() == 'y'
        if use_save_folder:
            if os.path.exists('savefolder.json'):
                with open('savefolder.json', 'r') as f:
                    save_folder_info = json.load(f)
                return save_folder_info
            else:
                save_folder = input("Please provide the path to the save folder: ").strip()
                save_interval = int(input("Please provide the interval (in minutes) for creating backups: ").strip())
                save_folder_info = {
                    'path': save_folder,
                    'interval': save_interval
                }
                with open('savefolder.json', 'w') as f:
                    json.dump(save_folder_info, f, indent=4)
                return save_folder_info
        else:
            return None

    def create_backup(self):
        if self.save_folder_info:
            save_folder = self.save_folder_info['path']
            backup_folder = os.path.join(save_folder, 'backups')
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_path = os.path.join(backup_folder, f'save_backup_{timestamp}')
            shutil.copytree(save_folder, backup_path)
            print(f"Backup created at {backup_path}")
        else:
            print("Save folder is not configured.")

    def find_target_window(self):
        print("Finding target window...")
        windows = gw.getAllWindows()
        for win in windows:
            print(f"Checking window: {win.title}")
            if self.program_name in win.title.lower():
                print(f"Found target window: {win.title}")
                self.target_window = win
                break
        if not self.target_window:
            print(f"No window found with the name containing '{self.program_name}'")

    def connect_to_twitch(self):
        server = 'irc.chat.twitch.tv'
        port = 6667
        token = f"oauth:{self.TWITCH_TOKEN}"
        nickname = self.TWITCH_USERNAME
        channel = self.CHANNEL

        print("Connecting to Twitch IRC...")
        sock = socket.socket()
        sock.connect((server, port))
        sock.send(f"PASS {token}\r\n".encode('utf-8'))
        sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
        sock.send(f"JOIN {channel}\r\n".encode('utf-8'))
        print("Twitch IRC connection established")

        return sock

    async def listen_for_messages(self):
        print("Listening for messages...")
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                response = await loop.run_in_executor(pool, self.sock.recv, 2048)
                response = response.decode('utf-8')
                print(f"Received response: {response}")
                if self.handle_ping_response(response):
                    continue
                user = self.parse_user(response)
                if user == "Nightbot" or user == "nightbot":
                    continue
                print(f"Parsed user: {user}")
                message = self.parse_message(response)
                print(f"Parsed message: {message}")
                if self.save_emulator(user, message):
                    continue
                if self.handle_save_command(user, message):
                    continue
                await self.process_twitch_plays_input(message)

    def save_emulator(self, user, message):
        if user == "ariasmoko" and message.strip().lower() == "!save-state":
            print("Saving state...")
            win32api.keybd_event(win32con.VK_F1, 0, 0, 0)
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_F1, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
            print("State saved!")
            return True
        return False

    def handle_save_command(self, user, message):
        if user in ["ariasmoko", "Insleight"] and message.strip().lower() == "!save":
            if self.save_folder_info:
                print(f"{user} issued !save command, creating backup...")
                self.create_backup()
            else:
                print("Save folder is not configured.")
            return True
        return False

    def handle_ping_response(self, response):
        if response.startswith('PING'):
            print("PING received, sending PONG")
            self.sock.send("PONG\n".encode('utf-8'))
            print("PONG sent")
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

    async def process_twitch_plays_input(self, command):
        if command is None:
            print("No command to process")
            return
        if self.target_window:
            if self.target_window.isMinimized:
                print("Restoring minimized window")
                self.target_window.restore()
                await asyncio.sleep(0.5)  # Give some time for the window to restore
                self.activate_window_with_retry(self.target_window)
                await asyncio.sleep(0.5)  # Give some time for the window to activate
        command = command.strip().lower()
        repetitions = self.get_repetitions(command)
        print(f"Processing command: {command}, repetitions: {repetitions}")
        if repetitions > 0:
            base_command = command[:len(command)//repetitions]
            if self.use_gamepad:
                await self.process_gamepad_input(base_command, repetitions)
            else:
                await self.process_keyboard_input(base_command, repetitions)

    def get_repetitions(self, command):
        match = re.match(r'([a-z]+)\1*', command)
        if match:
            print(f"Command match found: {match.group(1)}")
            return min(10, len(command) // len(match.group(1)))
        return 0

    async def process_keyboard_input(self, command, repetitions):
        print(f"Processing keyboard input: {command}, repetitions: {repetitions}")
        if command in self.key_map:
            vk_key = self.key_map[command]
            print(f"Sending key down: {vk_key}")
            win32api.keybd_event(vk_key, 0, 0, 0)
            await asyncio.sleep(.1 * repetitions)
            print(f"Sending key up: {vk_key}")
            win32api.keybd_event(vk_key, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            print(f"Key '{command}' not found in key map")

    async def process_gamepad_input(self, command, repetitions):
        print(f"Processing gamepad input: {command}, repetitions: {repetitions}")
        if command in self.controller_map:
            action = self.controller_map[command]
            print(f"Action: {action}")  # Debug print statement
            if isinstance(action, int):
                # Process button press
                button = action
                await self.press_button(button, repetitions)
            elif isinstance(action, str) and 'axis' in action:
                try:
                    _, axis, direction = action.split('_')
                    value = 32767 if direction == 'plus' else -32767
                    await self.move_axis(axis, value, repetitions)
                except ValueError as e:
                    print(f"Error splitting action: {action}, {e}")
            else:
                print(f"Unexpected action format: {action}")
        else:
            print(f"Action '{command}' not found in controller map")

    async def move_axis(self, axis, value, repetitions):
        print(f"Moving axis: {axis}, value: {value}, repetitions: {repetitions}")
        axis_id = {
            'x': pyvjoy.HID_USAGE_X,
            'y': pyvjoy.HID_USAGE_Y,
            'rx': pyvjoy.HID_USAGE_RX,
            'ry': pyvjoy.HID_USAGE_RY
        }.get(axis)
        if axis_id:
            self.j.set_axis(axis_id, value)
            await asyncio.sleep(0.1 * repetitions)
            self.j.set_axis(axis_id, 0x4000)

    async def press_button(self, button, repetitions):
        print(f"Pressing button: {button}, repetitions: {repetitions}")
        self.j.set_button(button, 1)
        await asyncio.sleep(0.1 * repetitions)
        self.j.set_button(button, 0)

if __name__ == "__main__":
    twitch_plays = TwitchPlays()
    loop = asyncio.get_event_loop()
    if twitch_plays.save_folder_info:
        async def backup_task():
            while True:
                interval = twitch_plays.save_folder_info['interval'] * 60
                await asyncio.sleep(interval)
                twitch_plays.create_backup()

        loop.create_task(backup_task())

    try:
        loop.run_until_complete(twitch_plays.listen_for_messages())
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        loop.close()
