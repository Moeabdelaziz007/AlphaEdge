       .__         .__            ___________.___               
_____  |  | ______ |  |__ _____   \_   _____/|   | ____   ____  
\__  \ |  | \____ \|  |  \\__  \   |    __)_ |   |/ ___\_/ __ \ 
 / __ \|  |_|  |_> >   Y  \/ __ \_ |        \|   / /_/  >  ___/ 
(____  /____/   __/|___|  (____  //_______  /|___\___  / \___  >
     \/     |__|        \/     \/         \/    /_____/      \/ 

**Localized. Zero-Cost. Privacy-First.**

---

## 🌟 Philosophy (فلسفة المعمارية)

Welcome to **alphaEdge**. In an era where Artificial Intelligence heavily relies on giant cloud infrastructures, **alphaEdge** redefines intelligence at the edge. Our architecture tackles the "Cognitive Bottleneck" not by bloating memory with massive models, but through **Cognitive Context Switching**.

Inspired by Google's latest **TurboQuant** paradigm (ICLR 2026), our engine addresses the final hurdle of edge computing: the KV Cache Bottleneck. By compressing the model's short-term memory (KV cache) locally, we massively accelerate contextual awareness. 

This enables a lightning-fast dual-memory system:
1. **Short-term Memory (TurboQuant-style KV Quantization):** Allows huge context handling in active memory without OOM crashes.
2. **Long-term Memory (sqlite-vec):** Fast local vector archives to store logic, code, and persona.

مرحباً بك في **alphaEdge**. هذا المشروع يحل "عنق الزجاجة الإدراكي" للأجهزة الطرفية (Edge Devices) بتكلفة صفرية وبدون سحابة. بالاعتماد على المبادئ الهندسية لأبحاث TurboQuant، ندمج بين **الضغط الجذري للذاكرة اللحظية (KV Cache)** وبين متانة **الذاكرة الموجهة (Vector DB)** لإنتاج محرك قادر على تحمل تبديل السياق (Context Switching) بأعلى كفاءة.

---

## ⚙️ The Cognitive Loop (دورة العمل)

The system emulates a top-tier AI team through three programmed states using a single SLM (Small Language Model):

1. **The Generator (المولد):** 
   Writes the initial draft or code freely with high creativity (`temperature: 0.7`).
2. **The Challenger (المتحدي):** 
   Critiques, debugs, and attacks the generated output to find logical flaws (`temperature: 0.1`, strict logical prompt).
3. **The Synthesizer (المُركّب):** 
   Integrates the Generator's draft with the Challenger's critique to produce a highly accurate, polished final result (`temperature: 0.3`).

---

## 🛠️ Recommended Tech Stack (التقنيات المقترحة)

Based on late-2025/2026 edge AI benchmarks, our core relies on:
- **Core Model:** `DeepSeek-R1-Distill-Qwen-1.5B-GGUF` or `Qwen-2.5-3B-GGUF` (Perfect balance of reasoning and local hardware efficiency).
- **Inference Engine:** `llama.cpp` via `llama-cpp-python` (Bare-metal C++ execution, highly optimized for Mac/PC without a heavy server overhead).
- **Memory Layer:** `sqlite-vec` (Lightweight local vector db for persistent embeddings, integrated natively into SQLite).

---

## 🚀 Quick Start (دليل البدء السريع)

**1. Clone the Repository:**
```bash
git clone https://github.com/Moeabdelaziz007/AlphaEdge.git
cd alphaEdge
```

**2. Setup Virtual Environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies:**
```bash
pip install -e .
```

**4. Download the Model:**
Place your preferred `.gguf` model into the `models/` directory.

**5. Ignite the Loop (MVP Execution):**
The project now supports full End-to-End Cognitive Loop execution via both a REST API and an Interactive CLI.

**Option A: AlphaEdge CLI (Terminal Interface)**
Run the AI directly via your terminal with zero-overhead:
```bash
# Interactive Mode
python src/cli.py

# Single-Shot Mode
python src/cli.py "Write a secure python script that creates a local hash vault."
```

**Option B: AlphaEdge Local API (FastAPI)**
Spin up the local backend to integrate extreme edge intelligence into your apps:
```bash
python api/main.py
# Or via uvicorn directly:
uvicorn api.main:app --reload
```
The API serves predictions via: `POST http://127.0.0.1:8000/api/v1/think`
Send payload:
```json
{
  "query": "How to optimize KV Cache on M-Series MacBooks?"
}
```

---

<br><br>
**Developed by Mohamed H Abdelaziz, Cybersecurity & AI architecture.**
