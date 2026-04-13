<p align="center">
  <img src="https://raw.githubusercontent.com/Moeabdelaziz007/AlphaEdge/main/assets/banner.png" alt="AlphaEdge Protocol Banner" width="100%">
</p>

# 🌌 AlphaEdge OS
**A Self-Aware, Edge-Native AI Engineer that Lives in your Codebase.**

AlphaEdge is not a chatbot. It is a persistent, state-aware Senior Software Engineer powered by a local-first **Super Meta-Loop** and holographic interfaces. It integrates seamlessly into your macOS / Apple Metal ecosystem, requiring absolutely $0 in cloud costs for its core reasoning engine.

---

## ⚡ Core Architecture (The Super Meta-Loop)

AlphaEdge achieves **Agentic Permanence**—the ability to act autonomously, modify itself, and anticipate developer actions—via these architectural pillars:

### 1. The Autonomous Heartbeat (Self-Improvment Loop)
AlphaEdge wakes up dynamically via a repeating background Cron job and reads the `heartbeat.md` directives. 
- It uses the `update_memory` internal tool to **autonomously rewrite its own heartbeat goals** upon completion.
- It delegates heavy coding tasks via **Jules AI Extracations**, but utilizes a **Wait & Verify Sub-Loop** to actively poll and monitor the GitHub Pull Request status before marking anything as completed. 

### 2. Predictive Indexing (The Clairvoyant Watcher)
AlphaEdge sports an active AST Watcher Daemon that constantly monitors the local filesystem.
- When you save modifications to any `.py` file, AlphaEdge calculates the "Blast Radius" of your changes (by scanning AST imports).
- It proactively pushes alerts directly to your Telegram: *"I noticed you modified the Engine. This impacts the Audio pipeline. Shall I review it?"*

### 3. Hyper-Resilient Intelligence Engine (`AIClient`)
- Integrated smart model cascading. When the primary Large Model (e.g., `llama-3.3-70b-versatile`) hits a 429 TPD limit, it silently falls back down the hierarchy without ever crashing the bot.

### 4. Zero-Latency Vision (Coming Soon: Apple MLX)
- Future architectures will utilize Apple MLX explicitly on macOS Unified Memory. This natively bypasses PCIe CPU/GPU bottlenecks, mimicking Apple's KV Cache 4-bit compressions to serve zero-latency holographic 3D UIs via our Telegram Mini App (TMA).

---

## 🚀 Execution Guide

1. Clone and ensure environment variables (`TELEGRAM_BOT_TOKEN`, `JULES_API_KEY`) are set in `.env`.
2. Ensure you have no generic terminal dependencies blocking execution (we run a raw Python AST parser to bypass system PIP locks).
3. Start the Meta-Loop Daemon:
```bash
python3 src/manager/bot.py
```
*(AlphaEdge will immediately bind to your Telegram Chat ID upon the first message. The Heartbeat & Watcher daemons will begin running silently in the background.)*

---
> *"We don't just build agents; we build digital teammates that remember, reason, and evolve alongside you."*
