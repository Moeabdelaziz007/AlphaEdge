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

We rely entirely on Local/Edge AI (using lightweight 1B to 3B parameter models in GGUF format) and avoid any dependence on cloud services, ensuring absolute privacy, zero latency, and $0 cost.

مرحباً بك في **alphaEdge**. هذا المشروع يحل "عنق الزجاجة الإدراكي" للأجهزة الطرفية (Edge Devices) بتكلفة صفرية، وبدون أي اعتماد على الخدمات السحابية لضمان الخصوصية المطلقة. نعتمد على استراتيجية "التبديل الإدراكي للسياق" باستخدام نماذج محلية خفيفة، حيث يتم تغيير الـ System Prompts وحالة الذاكرة برمجياً دون الحاجة لتحميل نماذج ضخمة.

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

**5. Ignite the Loop:**
```bash
# Example execution (coming soon in src/)
python src/core/engine.py
```

---

<br><br>
**Developed by Mohamed H Abdelaziz, Cybersecurity & AI architecture.**
