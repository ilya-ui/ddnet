#!/bin/bash

echo "🔧 Building LM Arena Chat Application..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed!"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv .venv
fi

echo "📦 Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "🏗️  Building executable with PyInstaller..."
pyinstaller --onefile --windowed --name "LMArena-Chat" --icon=NONE chat_app.py
status=$?

deactivate >/dev/null 2>&1

if [ $status -eq 0 ]; then
    echo ""
    echo "✅ Build completed successfully!"
    echo ""
    echo "📂 Executable location: dist/LMArena-Chat"
    echo ""
    echo "To run the application:"
    echo "  ./dist/LMArena-Chat"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
