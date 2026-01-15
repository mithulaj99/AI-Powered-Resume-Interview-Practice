# AI-Powered-Resume-Interview-Practice
AI-powered voice mock interview practice using your resume and job description
# AI Resume Interview Prep

**Voice-powered AI mock interviews using your own resume**  
Practice technical/behavioral interviews by *speaking* — no typing needed!

Questions are generated from your resume + job description  
→ Spoken to you via TTS  
→ You record answers by voice  
→ Automatic transcription shows what you said

Perfect for software engineering, data science, product management & tech interviews.



<p align="center">
  <img src="https://miro.medium.com/v2/resize:fit:1400/1*P8qc2MjAxHHFQZIyC2CJmw.png" alt="Voice interview practice flow" width="720">
  <br>
  <em>Realistic voice-based practice experience</em>
</p>

## ✨ Features

- 🎤 **Voice-only answers** — speak naturally, no typing
- 🔊 AI reads questions aloud using natural TTS (pyttsx3)
- 📄 Questions generated from **your resume** + job description
- ⚙️ Adjustable difficulty (Easy → Very Hard) & number of questions
- 📝 Automatic speech-to-text transcription of your answers
- 🧠 Powered by Groq + custom RAG for high-quality, relevant questions
- Clean & responsive Streamlit UI

(Coming soon: AI evaluation & detailed feedback on answers)

## 🚀 Live Demo


→ [Try it live on Streamlit Community Cloud](https://ai-powered-resume-interview-practice-5k2s9bvqph7aevphbhc4sw.streamlit.app/)  

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Voice**: pyttsx3 (TTS), browser audio input + Groq Whisper (STT)
- **AI**: Groq LLM + custom RAG wrapper
- **PDF parsing**: PyPDF2

## Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/AI-Resume-Interview-Prep.git
cd AI-Resume-Interview-Prep

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
