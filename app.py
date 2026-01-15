import streamlit as st
import PyPDF2
import pyttsx3
import io
import threading
from rag_wrapper import generate_project_questions_rag as generate_project_questions
from groq_service import evaluate_answer, transcribe_audio

# ─── Page Config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Voice Interview Practice",
    page_icon="🎤",
    layout="wide"
)

st.title("AI Voice Interview Practice")
st.caption("Questions spoken • Voice answers only • Mock interview")

# ─── TTS (non-blocking) ──────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_tts_engine():
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        return engine
    except Exception as e:
        st.error(f"TTS engine failed: {e}")
        return None

def speak_text(text: str):
    engine = get_tts_engine()
    if engine is None:
        return
    
    def run():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    
    threading.Thread(target=run, daemon=True).start()

# ─── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 Resume & Job", "⚙️ Settings"])

with tab1:
    st.subheader("Your Resume")
    resume_method = st.radio("How to provide resume:", ["Upload PDF", "Paste text"], horizontal=True)

    resume_content = ""
    if resume_method == "Upload PDF":
        file = st.file_uploader("Upload resume (PDF)", type=["pdf"])
        if file:
            try:
                pdf = PyPDF2.PdfReader(file)
                resume_content = "\n".join(page.extract_text() or "" for page in pdf.pages)
                if resume_content.strip():
                    st.success("Resume loaded")
            except Exception as e:
                st.error(f"PDF error: {e}")
    else:
        resume_content = st.text_area("Paste resume text...", height=180)

    st.subheader("Target Job Description")
    jd_content = st.text_area("Paste job description...", height=180)

# ─── Settings ────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns([3,2])
    with col1:
        focus = st.radio("Questions based on:", 
                        ["Resume only", "Job Description only", "Both (recommended)"], 
                        index=2)
    with col2:
        num_q = st.number_input("Number of questions", 1, 12, 5)
        difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard","Very Hard"], index=2)

# ─── Generate Questions ──────────────────────────────────────────────────
context = []
if resume_content.strip():    context.append(f"RESUME:\n{resume_content[:6000]}")
if jd_content.strip():        context.append(f"JOB:\n{jd_content[:6000]}")
full_context = "\n\n".join(context)

if st.button("✨ Generate Questions", type="primary", disabled=not full_context.strip()):
    with st.spinner("Generating..."):
        try:
            questions = generate_project_questions(
                resume_text=full_context,
                difficulty=difficulty.lower(),
                count=num_q
            )
            st.session_state.questions = questions
            st.success(f"{len(questions)} questions ready!")
        except Exception as e:
            st.error(f"Generation failed: {e}")

# ─── Interview Section ───────────────────────────────────────────────────
if "questions" in st.session_state and st.session_state.questions:
    st.divider()
    st.subheader(f"Voice Practice – {difficulty}")

    if "transcriptions" not in st.session_state:
        st.session_state.transcriptions = {}
    if "evaluations" not in st.session_state:
        st.session_state.evaluations = {}

    for i, q in enumerate(st.session_state.questions, 1):
        with st.expander(f"Question {i}", expanded=(i==1)):
            col1, col2 = st.columns([8,2])
            col1.markdown(f"**{q.question}**")
            
            if col2.button("🔊 Speak", key=f"spk_{i}"):
                speak_text(q.question)
                st.toast("Speaking...", icon="🔊")

            st.caption(f"{q.type} • ~{q.estimated_time_min} min")

            # ── Recording ────────────────────────────────────────────────
            st.markdown("**Record your answer**")
            audio = st.audio_input("Click to record 🎤", key=f"aud_{i}")

            if audio is not None:
                try:
                    audio_bytes = audio.getvalue()
                except Exception as e:
                    st.error(f"Cannot read audio data: {e}")
                    audio_bytes = None

                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")

                    key = f"audio_bytes_{i}"
                    if key not in st.session_state or st.session_state[key] != audio_bytes:
                        st.session_state[key] = audio_bytes

                        with st.spinner("Transcribing..."):
                            try:
                                transcript = transcribe_audio(audio_bytes)
                                st.session_state.transcriptions[i] = (transcript or "").strip()
                            except Exception as e:
                                st.error(f"Transcription failed: {e}")
                                st.session_state.transcriptions[i] = ""

            # Show transcription if available
            if i in st.session_state.transcriptions and st.session_state.transcriptions[i]:
                st.markdown("**Your transcribed answer:**")
                st.info(st.session_state.transcriptions[i])

            # ── Evaluation (placeholder - add when ready) ────────────────
            # if i in st.session_state.evaluations and st.session_state.evaluations[i]:
            #     st.markdown("**Evaluation:**")
            #     st.write(st.session_state.evaluations[i])

# ─── Reset ───────────────────────────────────────────────────────────────
st.divider()
if st.button("🔄 New Session"):
    for k in list(st.session_state.keys()):
        if k != "questions":
            del st.session_state[k]
    st.rerun()