# LM Arena Chat Application

A desktop application for chatting with AI models via lmarena.ai. Features a GUI built with `tkinter` and API integration using `requests`. Includes build scripts for creating standalone executables with `PyInstaller` (Windows/Linux/macOS).

## 🚀 Features
- Multiple AI model support (GPT-4, GPT-3.5 Turbo, Claude 3 Sonnet, Gemini Pro, etc.)
- User-friendly graphical interface with chat history
- Streaming response support
- Conversation reset/clear
- Single executable file compilation

## 📦 Installation and Running from Source
1. Install Python ≥ 3.10
2. Create and activate a virtual environment (recommended)
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the GUI application:
   ```bash
   python chat_app.py
   ```

   For terminal-based usage, a CLI version is available:
   ```bash
   python cli_chat.py
   ```

## 🏗️ Building Executable

### Linux / macOS
```bash
chmod +x build.sh
./build.sh
```

### Windows
```bat
build.bat
```

> **Note:** Build scripts automatically create and use a local `.venv` environment, so global dependency installation is not required.

The compiled binary will be available in the `dist/` folder.

## ⚙️ Settings
- Model selection: Use the dropdown menu in the top section
- Clear history: Click the "🗑️ Clear Chat" button
- Conversations start automatically with a new session; clearing chat resets the conversation

## 📁 Project Structure
```
├── chat_app.py           # Main GUI (tkinter)
├── cli_chat.py           # Terminal version
├── lmarena_api.py        # lmarena.ai API integration
├── requirements.txt      # Project dependencies
├── build.sh / build.bat  # Build scripts
├── README.md             # Russian documentation
└── README_EN.md          # English documentation
```

## 🛠️ Technical Details
- UI updates and response streaming implemented via separate `threading.Thread`
- Compilation uses `PyInstaller` with `--onefile` and `--windowed` flags
- API requests target the reverse-engineered endpoint `https://lmarena.ai/api/chat`

## ❗ Important
The reverse API may change response format over time. If issues arise, check the response format using browser developer tools (network tab) and adapt the JSON parsing in `lmarena_api.py` as needed.

Enjoy using LM Arena Chat! 🤖
