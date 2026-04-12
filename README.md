<div align="center">
  <h1>🚀 αlphaEdge</h1>
  <p><strong>Offline Cognitive Edge Engine | المحرك الإدراكي للذكاء الاصطناعي الطرفي</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
  [![Llama.cpp](https://img.shields.io/badge/Engine-llama.cpp-black)](https://github.com/ggerganov/llama.cpp)
  [![Edge AI](https://img.shields.io/badge/Priority-Zero_Cost_Privacy-success)](#)
</div>

<br/>

## 🌍 Overview | نظرة عامة

**[EN]** Welcome to **AlphaEdge**. In an era where Artificial Intelligence heavily relies on giant cloud infrastructures, AlphaEdge redefines autonomy at the edge. Our architecture tackles the RAM hardware shortage (the "Cognitive Bottleneck") not by bloating memory, but through an advanced Multi-Agent protocol dubbed **Cognitive Context Switching**. Simply put: we compress local memory and rapidly switch the persona of a single Small Language Model (SLM) to emulate an entire top-tier AI Dev Team. Zero clouds. Strict privacy. 

**[AR]** مرحباً بك في **AlphaEdge**. في عصر يعتمد فيه الذكاء الاصطناعي على البنية التحتية السحابية العملاقة، يعيد هذا المحرك تعريف الاستقلالية المطلقة عبر الأجهزة الطرفية. نحن نحل مشكلة "عنق الزجاجة المعرفي" وقصور الرامات ليس عبر تكبير النماذج، بل عبر بروتوكول متطور يُدعى **التبديل الإدراكي للسياق**. نقوم بضغط الذاكرة اللحظية وتحويل شخصية نموذج لغوي واحد صغير بسرعة البرق ليقوم بدور "فريق كامل" من المبرمجين. لا سحابات. خصوصية مطلقة.

---

## 🧠 Brain Architecture | الهندسة المعمارية للمحرك

**[EN]** The system relies on three interconnected pillars representing modern edge methodologies:
1. **TurboQuant Paradigm:** Inspired by late 2026 local tech, we compress short-term memory (KV Cache) aggressively to fit massive code reasoning directly onto Apple Metal GPUs without Out-Of-Memory crashes.
2. **Dual-Layer Memory:** While short-term memory handles the immediate context, `sqlite-vec` embeddings supply instantaneous RAG (Retrieval-Augmented Generation) Long-Term memory.
3. **VibeVoice Integration:** Zero-latency Voice Activity Detection (VAD) coupled with asynchronous "thought markers" (System says: "Let me analyze...") masking the heavy CPU background processing.

**[AR]** يعتمد النظام على ثلاثة أعمدة تمثل أحدث منهجيات حوسبة الحافة (Edge AI):
1. **برادايم TurboQuant:** نضغط الذاكرة اللحظية (KV Cache) بشراسة لتستوعب الأكواد الطويلة مباشرة على معالجات (Apple Metal) دون انهيار النظام.
2. **الذاكرة المزدوجة:** بينما تشرف الذاكرة اللحظية على السياق الحالي، تقوم قاعدة `sqlite-vec` بتمثيل ذاكرة طويلة الأمد للتذكر اللحظي عبر الـ Embeddings.
3. **تكامل VibeVoice:** نظام التقاط صوتي لحظي خالٍ من التأخير يطلق رسائل مسكنة للمستخدم لتغطية وقت طحن البيانات المعقد بواسطة الوكلاء في الخلفية.

### ⛓️ The Cognitive Flow Diagram | مخطط سير العمل

```mermaid
graph TD
    User((User 🎙️ Voice/Text)) --> Pipeline[⚙️ AlphaEdge Pipeline]
    
    subgraph Local Data Security
        Pipeline <--> Memory[(sqlite-vec Vector DB + Nomic-Embed)]
    end

    subgraph The Cognitive Loop 🧠
      Generator[💡 Generator Agent]
      Challenger[🤺 Challenger Agent]
      Synthesizer[🧩 Synthesizer Agent]
      
      Generator -- "Draft (Temp 0.7)" --> Challenger
      Challenger -- "Critique (Temp 0.1)" --> Synthesizer
      Synthesizer -- "Perfect Result (Temp 0.3)" --> Pipeline
    end

    Pipeline --> Generator
    Pipeline --> VibeVoice[🔊 VibeVoice Text-To-Speech]
    VibeVoice --> SystemTalk((AlphaEdge Voice))
    
    classDef secure fill:#0f172a,stroke:#3b82f6,color:#fff;
    classDef agent fill:#1e1e2f,stroke:#a855f7,color:#fff;
    class Memory,Pipeline secure;
    class Generator,Challenger,Synthesizer agent;
```

---

## 🛠️ Tech Stack | حزمة التقنيات

| Component / المكون               | Technology / التقنية | Details / التفاصيل |
|---------------------------------|-----------------------|-------------------|
| **Core Intelligence العقل**    | `Qwen 2.5 1.5B GGUF`  | High reasoning logic per parameter (Best for Coding/Logic). |
| **Inference Engine المحرك**    | `llama-cpp-python`    | Apple Metal HW Acceleration & KV Cache Optimization. |
| **Memory Database الذاكرة** | `sqlite-vec`          | Lightning fast vector search locally without server overhead. |
| **Backend API الخادم**     | `FastAPI` / `Uvicorn` | REST infrastructure for modular app integrations. |
| **Speech Module النظام الصوتي**| `SpeechRecognition`   | High-efficiency VAD bridging to native OS text-to-speech. |

---

## 🚀 Quick Start | دليل البدء السريع

**[EN]** Deploying the MVP requires no cloud keys—just raw local execution power.
**[AR]** تشغيل النظام لا يتطلب أي مفاتيح سحابية — فقط قوة جهازك.

**1. Clone & Env / نسخ المستودع وتهيئة البيئة**
```bash
git clone https://github.com/Moeabdelaziz007/AlphaEdge.git
cd alphaEdge
python3 -m venv .venv && source .venv/bin/activate
```

**2. Bypass Compile Load / تجاوز البناء وتثبيت المحرك**
```bash
# Mac Metal Accelerated Build
pip install "llama-cpp-python>=0.2.77" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
pip install -e .
```

**3. Download Local Intelligence / جلب الوعي الاصطناعي**
```bash
# Downloads Qwen-1.5B & Nomic-Embed (Run Once)
python scripts/setup_models.py
```

**4. Ignite the Systems / إطلاق النظام**

**Option A: The Live Voice Agent (CLI)**
```bash
python src/cli.py --live
```

**Option B: REST API Developer Backend**
```bash
uvicorn api.main:app --reload
# Access Swagger UI natively at http://127.0.0.1:8000/docs
```

---

## 🗺️ Roadmap | خارطة الطريق المفتوحة
- [x] Phase 1: Core SLM Pipeline & KV compression.
- [x] Phase 2: Cognitive Agents (Generator, Challenger, Synthesizer).
- [x] Phase 3: VibeVoice Asynchronous Voice Agent & CLI.
- [ ] Phase 4: Local Desktop GUI (Next.js/Tauri integration).

<br>

<div align="center">
  <p>Engineered with <strong>First Principles Thinking</strong> by</p>
  <h3>Mohamed H Abdelaziz</h3>
  <p><em>Cybersecurity & AI Architecture</em></p>
</div>
