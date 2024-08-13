# Chat Audio Generator

This project is a Twitch chat audio generator that uses RealTimeTTS to convert Twitch chat messages into audio. It allows for the customization of voices and applies various text filters to modify or block specific types of messages.

## Features

- **Twitch Chat Integration:** Connects to Twitch chat and listens for messages.
- **Real-Time Text-to-Speech (TTS):** Converts chat messages into audio using the Coqui TTS engine.
- **Customizable Voice Profiles:** Allows loading and switching between different voice profiles for users.
- **Text Filters:** Includes several text filters to remove unwanted messages, such as URLs, empty messages, or spam.
- **Configurable via JSON:** Supports external configuration files (`user_voice.json` and `replacements.json`) for user-specific voices and text replacements.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/chat-audio-generator.git
   cd chat-audio-generator
   ```

2. **Install Dependencies:**

   Install the required Python packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

   Ensure that you have the `RealTimeTTS` package installed, which is required for the TTS engine.

3. **Environment Configuration:**

   Create a `.env` file in the root of the project and add your Twitch API secret:

   ```env
   TWITCH_API_SECRET=your_twitch_oauth_token
   ```

   Set your Twitch username and channel in the `ChatAudioGenerator` class.

4. **Configure Voice Profiles:**

   Create a `user_voice.json` file to map users to specific voices. Example:

   ```json
   {
       "username1": "voice1",
       "username2": "voice2"
   }
   ```

5. **Configure Text Replacements:**

   Create a `replacements.json` file to define simple replacements and regex-based replacements. Example:

   ```json
   {
       "simple": {
           "badword": "goodword"
       },
       "regex": {
           "\\bbadword\\b": "goodword"
       }
   }
   ```

## Usage

1. **Start the Application:**

   Run the `ChatAudioGenerator` to connect to Twitch and start processing messages:

   ```bash
   python chat_audio_generator.py
   ```

2. **Customize Filters:**

   You can add or modify text filters in the `ChatAudioGenerator` class to fit your specific needs.

## Dependencies

- Python 3.x
- `RealTimeTTS`
- `dotenv`
- `sounddevice`

Ensure that you have the appropriate Coqui TTS model and sound device configuration.

## Troubleshooting

- **Error: `user_voice.json` does not exist:** Ensure that you've created the `user_voice.json` file with valid user-voice mappings.
- **TTS Model Issues:** Verify that the TTS model path is correct and that the model files are in the specified directory.
- **Twitch Connection Problems:** Make sure your Twitch OAuth token is valid and correctly set in the `.env` file.

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

Feel free to customize the sections as needed for your project!
