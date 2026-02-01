Technical Design Document: PocketClaw

Component: Desktop Agent / Mobile Interface
Version: 1.1 (Web Pairing Added)

1. System Architecture

PocketClaw operates as a single-binary daemon running on the host machine (User's Laptop/Server). It acts as a bridge between the Telegram Bot API and the local operating system shell.

High-Level Data Flow

Input: User sends message via Telegram App OR interacts via Local Web Dashboard.

Transport: Telegram Cloud -> PocketClaw Daemon (via HTTPS Long-Polling).

Routing:

Command Router: Intercepts specific commands (/start, /kill).

Agent Engine: Pipes natural language to LLM/Interpreter.

Execution: Python executes system calls (subprocess, os, pyautogui).

Output: Logs/Files/Video sent back to Telegram Cloud -> User.

2. Interface Specifications (Telegram)

The interface relies on a persistent ReplyKeyboardMarkup. We have removed the explicit "Hype" tab in favor of natural language triggers.

2.1 Persistent Command Deck

🟢 Status

📁 Fetch

🧠 Agent Mode

🛑 Panic

2.2 Control Logic

🟢 Status: Triggers system_tools.get_stats() → Returns text report.

📁 Fetch: Triggers file_manager.list_dir(current_path) → Returns InlineKeyboard navigation.

🧠 Agent Mode: Toggles STATE = AGENT_ACTIVE. Hides buttons, enables free-text input.

🛑 Panic: Triggers process_manager.emergency_kill() → Hard kills agent subprocesses.

3. Module Specifications

The application codebase is divided into five core modules.

3.1 bot_gateway.py (The Listener)

Library: python-telegram-bot (Async).

Responsibility:

Handles Long-Polling (updater.start_polling()).

Auth Gate: Middleware that checks update.effective_user.id against ALLOWED_USER_ID. Drops unauthorized traffic.

Router: Directs traffic to system_tools or agent_runtime.

3.2 web_server.py (The Pairing Bridge)

Library: FastAPI + Uvicorn (Lightweight).

Port: 8888 (Default).

Responsibility:

Serves the Pairing Dashboard at http://localhost:8888.

Generates a dynamic QR Code using qrcode library.

Deep Link: The QR code encodes https://t.me/YourBotName?start=<SESSION_SECRET>.

Handshake: When the user scans the QR and taps Start on Telegram, bot_gateway validates the <SESSION_SECRET> and saves the User's Chat ID as the ALLOWED_USER_ID.

3.3 agent_runtime.py (The Brain)

Library: open-interpreter (Python Interface).

Configuration:

auto_run = True (No human confirmation step).

offline = False (Allow API usage if configured).

Context Window: Maintains a sliding window of the last 10 interactions.

Tool Access: Gives the LLM explicit access to media_engine tools (see 3.5).

3.4 system_tools.py (The Hands)

Stats: Uses psutil to fetch CPU load, RAM usage, and uptime.

Files: Uses pathlib for directory traversal.

Constraint: ROOT_DIR defaults to User Home. os.pardir (..) is blocked if attempting to go above Home (basic jail).

Vision: Uses pyautogui.screenshot() and cv2 (OpenCV) to capture webcam frames.

3.5 media_engine.py (The "Hype" Capability)

This module provides tools for the Agent to "market itself" upon request.

Tool: start_screen_recording(filename)

Spawns a background thread using cv2.VideoWriter grabbing screen frames.

Tool: stop_screen_recording()

Finalizes the .mp4 file.

Tool: generate_voiceover(text)

Uses edge-tts (Microsoft Edge Text-to-Speech) to generate high-quality .mp3 files locally.

Tool: compile_video(video_path, audio_path)

Uses ffmpeg-python (or moviepy) to merge the screen recording with the voiceover track.

4. Pairing & Setup Flow (The Web QR)

This flow ensures "Normies" never touch a config file.

Install: User runs PocketClaw.exe.

Auto-Launch: The app opens the default browser to http://localhost:8888.

Display: A clean web page shows:

"PocketClaw is Ready."

A large QR Code.

Text: "Scan with your phone camera to connect Telegram."

Action: User scans QR.

Redirect: Phone opens Telegram App -> Presses "Start".

Lock: The Desktop App detects the handshake, saves the User ID, and shuts down the Web Server (for security).

5. Agent Tool Definitions (JSON Schema)

The Agent (Open Interpreter) is initialized with these custom tools to enable the "Self-Marketing" features naturally.

[
{
"function": "record_task",
"description": "Records the screen while executing a task, adds a voiceover, and returns the video file.",
"parameters": {
"type": "object",
"properties": {
"task_description": {
"type": "string",
"description": "What you are doing, for the voiceover script."
},
"duration": {
"type": "integer",
"description": "Expected duration in seconds."
}
}
}
}
]

Usage Example:

User: "Run the payroll script and make a hype video about it."

Agent: Calls record_task(task_description="Running payroll automation...").

System: Starts recording -> Runs script -> Generates TTS -> Merges -> Sends Video.

6. Security & Safety Mechanisms

6.1 The "Panic" Switch

Since the Agent has shell access, we need a hard kill switch.

Mechanism: The 🛑 Panic button operates on a separate thread.

Action:

Sets global STOP_SIGNAL = True.

Iterates through psutil.Process(pid).children() of the Agent runtime.

Sends SIGKILL to all child processes immediately.

Resets Agent Context.

6.2 File System Jail (Soft)

The file_manager module strictly validates paths.

if not os.path.abspath(path).startswith(home_dir): raise AccessDenied

7. Deployment Strategy

7.1 Environment Variables (.env)

TELEGRAM_BOT_TOKEN="1234:ABC..."
ALLOWED_USER_ID="999888777"
OPENAI_API_KEY="sk-..." # Or ANTHROPIC_API_KEY / LOCAL_LLM_URL

7.2 Build Process (PyInstaller)

To ensure the "Dusty Laptop" compatibility, we compile to a standalone executable.

build_spec.spec configuration:

Hidden Imports: pydantic, tiktoken, moviepy.audio.fx.all, uvicorn, fastapi.

Data Files: Include ffmpeg binary if not assuming system install.

Command: pyinstaller --onefile --noconsole --name PocketClaw main.py
