# AutoShorts AI — Local Video to Shorts Generator

AutoShorts AI is a self-hosted, 100% free, and CPU-compatible automated tool designed to convert long-form horizontal videos into short-form vertical clips (9:16) with burned-in animated captions.

This repository contains the foundational environment, baseline architecture, and system configurations required for the project pipeline to execute successfully.

---

## 🚀 Tasks Performed (Project Foundation)

As part of the initial core setup, the following milestones have been successfully completed:
1. **Repository & Version Control Initialization:** Configured the basic Git repository and synchronized the codebase with GitHub.
2. **Standard Modular Directory Layout:** Built the production-grade folder structure separating application templates, static assets, and modular data processing components.
3. **Environment Security & Cleanup Rules:** Integrated a robust `.gitignore` strategy ensuring system caches (`.vscode/`, `__pycache__/`) and local video buffers (`uploads/`, `shorts_output/`) remain untracked while maintaining folder schemas on remote branches via `.gitkeep`.
4. **Dependency Architecture:** Defined the exact base Python package distributions, anchoring core modules like `Flask`, `faster-whisper`, and rendering frameworks with rigid version pins to avoid pipeline breakage.
5. **System Engine Mapping (FFmpeg integration):** Evaluated and successfully mapped the system-level binaries for FFmpeg, anchoring native command structures to drive rapid media decoding, audio extractions, and multi-threaded video processing filters.

---

## 📂 Project Architecture

The workspace layout is structured as follows:

```text
autoshorts/
│
├── pipeline/               # Modular pipeline components
│   ├── transcriber.py      # Audio extraction & speech-to-text processing
│   ├── scorer.py           # Importance scoring metrics
│   ├── selector.py         # Sub-clip window boundaries
│   ├── renderer.py         # 9:16 vertical crop adjustments
│   └── effects.py          # Dynamic styling & render fallbacks
│
├── static/                 # Frontend styling and scripts
│   ├── style.css
│   └── app.js
│
├── templates/              # HTML standard user interface templates
│   └── index.html
│
├── uploads/                # Temporary processing directory for source media
├── shorts_output/          # Generated output path for final vertical video clips
├── app.py                  # Main Flask application entrypoint
├── requirements.txt        # Production Python library specifications
├── .gitignore              # Environment file locking
└── README.md               # Infrastructure documentation

🛠️ Local Environment Setup Guide
Follow these sequential steps to safely recreate and host the established environment structure on your machine:

1. Clone the Workspace
Open your terminal or command prompt and clone this centralized repository:
git clone https://github.com/Ammarawan123/autoshorts
cd autoshorts
2. Isolate with a Virtual Environment
Initialize a clean Python virtual environment to host the project-specific assemblies independently from system-wide environments.

On Windows (Command Prompt):

  python -m venv venv
  venv\Scripts\activate
2. Isolate with a Virtual Environment
Initialize a clean Python virtual environment to host the project-specific assemblies independently from system-wide environments.

On Windows (Command Prompt):


  python -m venv venv
  venv\Scripts\activate
