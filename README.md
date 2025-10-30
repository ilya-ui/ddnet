# Phone ↔ PC Messenger

This repository contains a small proof-of-concept messenger that allows exchanging
text messages between an Android phone and a Windows PC (or any other desktop
OS) over the same network.

The solution is composed of two parts:

1. **Relay server** (`server/relay_server.py`) – a lightweight WebSocket server
   that relays messages between connected clients.
2. **Cross-platform client** (`app/main.py`) – a Kivy-based graphical
   application that connects to the relay server. The same code base can be
   packaged into a Windows `.exe` using PyInstaller or into an Android `.apk`
   using Buildozer.

> **Note:** Compiled binaries are not included in the repository. Follow the
> packaging guides below to produce your own `.exe` and `.apk` files.

## Features

- Simple WebSocket relay server with in-memory message history.
- Real-time text chat between multiple clients.
- Cross-platform Kivy client with a basic chat interface.
- Automatic reconnection attempts when the connection drops.
- Works across devices as long as they can reach the relay server over the
  network (e.g. local Wi‑Fi, VPN, etc.).

## Project structure

```
/home/engine/project
├── app
│   ├── main.py              # Kivy UI application (desktop + mobile)
│   ├── requirements.txt     # Client Python dependencies
│   └── buildozer.spec.example  # Example Buildozer configuration template
├── server
│   ├── relay_server.py      # Async WebSocket relay server
│   └── requirements.txt     # Server Python dependencies
├── README.md
└── .gitignore
```

## 1. Running the relay server

The relay server is written with `asyncio` and the `websockets` package.

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
python relay_server.py --host 0.0.0.0 --port 8765
```

By default the server listens on `0.0.0.0:8765`. Clients should use the IP
address (or hostname) of the machine where the server is running. If you run the
server on your PC and want to connect from a phone on the same Wi‑Fi network,
enter the PC's LAN IP address inside the client app.

## 2. Running the client on the desktop (development mode)

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

When prompted, provide a display name (e.g. `PC`) and the address of the relay
server (e.g. `192.168.1.42`) along with the port (default `8765`).

## 3. Packaging the desktop client into an `.exe`

1. Ensure you have a working Python environment on Windows with all dependencies
   installed (`pip install -r app/requirements.txt`).
2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
3. Build the executable from the project root (Windows PowerShell / CMD):
   ```bash
   cd app
   pyinstaller --name phone_pc_messenger --onefile --windowed main.py
   ```
4. The resulting executable will be located in `app/dist/phone_pc_messenger.exe`.

For custom icons or additional data files, adjust the PyInstaller options as
needed.

## 4. Packaging the client into an Android `.apk`

Packaging for Android requires Linux or WSL with Buildozer. The following steps
use the included `buildozer.spec.example` file as a starting point.

1. Install Buildozer and its dependencies (refer to the Buildozer documentation
   for your operating system).
2. From the repository root, copy the example spec file:
   ```bash
   cd app
   cp buildozer.spec.example buildozer.spec
   ```
3. Review and adjust `buildozer.spec` as necessary (e.g. update package name,
   permissions, icons).
4. Build the APK:
   ```bash
   buildozer android debug
   ```
5. The generated APK will be available in `app/bin/`.

For production builds and signing, consult the Buildozer documentation.

## Configuration tips

- Ensure all devices are connected to the same network or that appropriate
  firewall rules allow access to the chosen port.
- The relay server stores messages only in memory. Restarting the server clears
  the history.
- You can run multiple clients simultaneously; every message is broadcast to all
  connected clients.

## Troubleshooting

- **Cannot connect from phone:** Double-check that the server machine's firewall
  allows incoming connections on the chosen port. Use the LAN IP address, not
  `127.0.0.1`, when connecting from another device.
- **Slow or delayed messages:** Network latency or packet loss can cause
  delays. Ensure both devices have a stable connection.
- **Packaging errors:** Verify that Buildozer (for Android) or PyInstaller (for
  Windows) dependencies are installed and compatible with your Python version.

## License

This project is provided as-is without warranty. Feel free to extend or modify
it to suit your needs.
