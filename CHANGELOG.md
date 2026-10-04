# 📜 Changelog

All notable changes to pulse are documented here.  
Format loosely based on [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- Nothing yet — this is where your PR goes `(◕‿◕)`

### Changed
- 

### Fixed
- 

---

## [1.0.0] — 2026-10-XX

### Added
- ✨ Initial release
- 🔮 Floating always-on-top dashboard
- 🧠 Real AI model count via Ollama's `/api/ps`
- ⚡ Real tokens/sec parsed from `ollama.log` (identical to terminal)
- 💬 Built-in streaming chat window
- 🎨 4 shapes: circle, squircle, hex, diamond
- 📏 Custom resize from 200px → 600px with live font scaling
- ⚙️ Floating settings panel
- 🌈 Cyberpunk cyan/blue palette
- 🚫 Zero-terminal startup (self-manages Ollama)
- 🖥️ Windows 7 / 8 / 10 / 11 support
- 📝 Friendly README with mermaid diagrams

### Known issues
- First launch takes ~3 seconds (killing old Ollama + spawning serve)
- Only works with Ollama for now (LM Studio / vLLM coming soon)
- On very old GPUs, tokens/sec can drop below 1 (still real numbers!)

---

## 🚧 How to add an entry

When you submit a PR, add your change under `[Unreleased]` in the right section. We'll bump versions on release.

**Categories:**
- `Added` — new features
- `Changed` — changes to existing behavior
- `Deprecated` — soon-to-be-removed
- `Removed` — gone forever
- `Fixed` — bug fixes
- `Security` — vulnerability fixes
