import streamlit as st
from pypdf import PdfReader
from datetime import datetime, date
import pandas as pd
import random
import re
import os
import json

from groq import Groq
from dotenv import load_dotenv

st.set_page_config(
    page_title="StudyPilot AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
print(load_dotenv())
print(os.getenv("GROQ_API_KEY"))
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

if "notes" not in st.session_state:
    st.session_state.notes = ""

if "flashcards" not in st.session_state:
    st.session_state.flashcards = []

if "quiz" not in st.session_state:
    st.session_state.quiz = []

if "progress" not in st.session_state:
    st.session_state.progress = 0
if "card_index" not in st.session_state:
    st.session_state.card_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "xp" not in st.session_state:
    st.session_state.xp = 0

if "level" not in st.session_state:
    st.session_state.level = 1

if "streak" not in st.session_state:
    st.session_state.streak = 1

if "badges" not in st.session_state:
    st.session_state.badges = []

if "subjects" not in st.session_state:
    st.session_state.subjects = []
def ai_flashcards(text):

    prompt = f"""
You are an expert teacher.

Read the notes below.

Generate exactly 20 flashcards.

Return ONLY valid JSON.

Format:

[
    {{
        "question":"...",
        "answer":"..."
    }}
]

Notes:

{text[:12000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],
        temperature=0.3
    )

    reply = response.choices[0].message.content

    return json.loads(reply)

def add_xp(amount):

    st.session_state.xp += amount

    new_level = st.session_state.xp // 250 + 1

    if new_level > st.session_state.level:

        st.balloons()

        st.success(f"🎉 LEVEL UP! Level {new_level}")

        st.session_state.level = new_level
def read_pdf(uploaded_file):

    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    return text


def split_sentences(text):

    return re.split(r'(?<=[.!?])\s+', text)


def extract_keywords(text):

    words = re.findall(r"[A-Za-z]{5,}", text)

    ignore = {
        "which","their","there","these",
        "about","would","could","should",
        "where","after","before","because",
        "while","between","every","other",
        "those","being","having","chapter",
        "figure","table"
    }

    keywords = []

    for word in words:

        word = word.lower()

        if word not in ignore:

            keywords.append(word)

    keywords = sorted(list(set(keywords)))

    return keywords


def create_flashcards(text):

    cards = []

    sentences = split_sentences(text)

    patterns = [
        ("is", "What is {}?"),
        ("are", "What are {}?"),
        ("defined as", "How is {} defined?"),
        ("known as", "What is known as {}?"),
        ("called", "What is called {}?"),
        ("measured in", "What is {} measured in?")
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 25:
            continue

        sentence = re.sub(r"\s+", " ", sentence)

        matched = False

        for keyword, template in patterns:

            regex = rf"\b(.+?)\b\s+{re.escape(keyword)}\s+(.+)"

            m = re.search(regex, sentence, flags=re.IGNORECASE)

            if m:

                subject = m.group(1).strip(" .,:;()")
                answer = m.group(2).strip(" .,:;()")

                if len(subject) > 2 and len(answer) > 2:

                    cards.append({
                        "question": template.format(subject),
                        "answer": answer
                    })

                matched = True
                break

        if matched:
            continue

        if "=" in sentence:

            parts = sentence.split("=",1)

            if len(parts) == 2:

                left = parts[0].strip()
                right = parts[1].strip()

                if left and right:

                    cards.append({
                        "question": f"What does {left} equal?",
                        "answer": right
                    })

            continue

        if ":" in sentence:

            parts = sentence.split(":",1)

            if len(parts)==2:

                cards.append({
                    "question": f"What is {parts[0].strip()}?",
                    "answer": parts[1].strip()
                })

    unique = []

    seen = set()

    for card in cards:

        q = card["question"]

        if q not in seen:

            seen.add(q)

            unique.append(card)

    random.shuffle(unique)

    return unique[:50]
def ai_summary(text):

    prompt = f"""
You are an expert CBSE/JEE teacher.

Read these notes.

Create a study summary.

Include:

1. Chapter overview

2. Important concepts

3. Important formulas

4. Important definitions

5. Common exam questions

6. Last-minute revision tips

Keep it well formatted using markdown.

Notes:

{text[:12000]}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.3
    )

    return response.choices[0].message.content
def ask_ai(notes, question):

    prompt = f"""
You are StudyPilot AI.

Answer ONLY using the uploaded notes.

If the answer is not present in the notes,
say:

'I couldn't find that in your uploaded notes.'

Notes:

{notes[:12000]}

Student Question:

{question}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.2
    )

    return response.choices[0].message.content
def create_quiz(text):

    questions = []

    cards = create_flashcards(text)

    for card in cards:

        questions.append({
            "question": card["question"],
            "answer": card["answer"]
        })

    return questions[:15]


st.sidebar.title("📚 StudyPilot AI")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📄 Upload Notes",
        "📖 Notes",
        "📝 AI Summary",
        "💬 Ask AI",
        "🧠 Flashcards",
        "❓ Quiz",
        "📅 Timetable",
        "📊 Progress"
    ]
)

if page == "🏠 Dashboard":

    st.title("📚 StudyPilot AI")

    st.caption("Learn Smarter. Stress Less.")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "🏆 Level",
            st.session_state.level
        )

    with c2:
        st.metric(
            "⭐ XP",
            st.session_state.xp
        )

    with c3:
        st.metric(
            "📚 Flashcards",
            len(st.session_state.flashcards)
        )

    with c4:
        st.metric(
            "❓ Quiz",
            len(st.session_state.quiz)
        )

    with c5:
        st.metric(
            "📈 Progress",
            f"{st.session_state.progress}%"
        )
        st.subheader("⭐ XP Progress")

        current = st.session_state.xp % 250

        st.progress(current / 250)

        st.write(
            f"{current}/250 XP until Level {st.session_state.level + 1}"
        )

        st.divider()

        st.subheader("Today's Goal")

        st.progress(st.session_state.progress / 100)

        st.info(
            "Upload notes, generate flashcards, complete quizzes, and build your personalized timetable."
        )

elif page == "📄 Upload Notes":

    st.title("📄 Upload Notes")

    uploaded = st.file_uploader(
        "Upload your PDF Notes",
        type=["pdf"]
    )

    if uploaded:

        text = read_pdf(uploaded)

        st.session_state.notes = text

        try:

            st.session_state.flashcards = ai_flashcards(text)

        except Exception as e:

            st.warning(f"AI failed, using offline flashcards.\n\n{e}")

            st.session_state.flashcards = create_flashcards(text)

        st.session_state.quiz = create_quiz(text)

        add_xp(50)

        st.success("✅ +50 XP")

        st.success("✅ Notes uploaded successfully!")

        with st.expander("Preview Notes"):

            st.text_area(
                "Preview",
                text[:5000],
                height=350
            )

        st.info(
            f"Generated {len(st.session_state.flashcards)} flashcards and {len(st.session_state.quiz)} quiz questions."
        )


elif page == "📖 Notes":

    st.title("📖 Notes Viewer")

    if st.session_state.notes == "":

        st.warning("Upload a PDF first.")

    else:

        keyword = st.text_input(
            "🔍 Search your notes"
        )

        if keyword:

            lines = st.session_state.notes.split("\n")

            found = False

            for line in lines:

                if keyword.lower() in line.lower():

                    st.success(line)

                    found = True

            if not found:

                st.error("No matches found.")

        else:

            st.text_area(
                "Complete Notes",
                st.session_state.notes,
                height=600
            )

        st.download_button(
            "📥 Download Extracted Notes",
            st.session_state.notes,
            file_name="notes.txt"
        )
elif page == "📝 AI Summary":

    st.title("📝 AI Study Summary")

    if st.session_state.notes == "":

        st.warning("📄 Upload notes first.")

    else:

        if st.button("✨ Generate AI Summary"):

            with st.spinner("🤖 Reading your notes..."):

                try:

                    summary = ai_summary(
                        st.session_state.notes
                    )

                    st.markdown(summary)

                    add_xp(20)

                except Exception as e:

                    st.error(f"AI Error:\n\n{e}")

elif page == "💬 Ask AI":

    st.title("💬 Ask StudyPilot")

    if st.session_state.notes == "":

        st.warning("📄 Upload notes first.")

    else:

        question = st.text_input(
            "Ask anything about your notes..."
        )

        if st.button("🚀 Ask AI"):

            with st.spinner("🤖 Thinking..."):

                answer = ask_ai(
                    st.session_state.notes,
                    question
                )

            st.success(answer)

            add_xp(15)
elif page == "🧠 Flashcards":

    st.title("🧠 Flashcards")

    if len(st.session_state.flashcards) == 0:

        st.warning("Upload notes first.")

    else:

        if "card_index" not in st.session_state:
            st.session_state.card_index = 0

        if "show_answer" not in st.session_state:
            st.session_state.show_answer = False

        total = len(st.session_state.flashcards)

        card = st.session_state.flashcards[
            st.session_state.card_index
        ]

        st.markdown("""
<style>

.flash-container{
    display:flex;
    justify-content:center;
    margin-top:30px;
    margin-bottom:20px;
}

.flash-card{
    width:700px;
    min-height:330px;
    border-radius:25px;
    padding:40px;
    background:linear-gradient(135deg,#0f172a,#1e293b);
    color:white;
    box-shadow:0px 15px 35px rgba(0,0,0,.45);
    transition:all .35s ease;
    border:1px solid rgba(255,255,255,.08);
}

.flash-card:hover{
    transform:translateY(-6px) scale(1.02);
}

.flash-title{
    text-align:center;
    color:#38bdf8;
    font-size:18px;
    font-weight:bold;
}

.flash-question{
    margin-top:40px;
    text-align:center;
    font-size:30px;
    font-weight:700;
    line-height:1.5;
}

.answer-card{
    width:700px;
    min-height:170px;
    border-radius:20px;
    padding:30px;
    background:linear-gradient(135deg,#065f46,#047857);
    color:white;
    margin:auto;
    margin-top:20px;
    text-align:center;
    box-shadow:0px 10px 25px rgba(0,0,0,.4);
}

.answer-title{
    color:#6ee7b7;
    font-size:20px;
    font-weight:bold;
}

.answer-text{
    margin-top:20px;
    font-size:28px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

        st.markdown(f"""
<div class="flash-container">

<div class="flash-card">

<div class="flash-title">

🧠 Flashcard {st.session_state.card_index+1} / {total}

</div>

<hr>

<div class="flash-question">

{card["question"]}

</div>

</div>

</div>
""", unsafe_allow_html=True)        
    if st.button("👀 Reveal Answer", use_container_width=True):

            st.session_state.show_answer = True

            add_xp(5)

    if st.session_state.show_answer:

        st.markdown(f"""
<div class="answer-card">

<div class="answer-title">

✅ ANSWER

</div>

<div class="answer-text">

{card["answer"]}

</div>

</div>
""", unsafe_allow_html=True)

        st.write("")

        col1, col2, col3 = st.columns([1,1,1])

        with col1:

            if st.button("⬅ Previous", use_container_width=True):

                st.session_state.card_index = (
                    st.session_state.card_index - 1
                ) % total

                st.session_state.show_answer = False

                st.rerun()

        with col2:

            if st.button("🔀 Shuffle", use_container_width=True):

                random.shuffle(
                    st.session_state.flashcards
                )

                st.session_state.card_index = 0

                st.session_state.show_answer = False

                st.rerun()

        with col3:

            if st.button("Next ➡", use_container_width=True):

                st.session_state.card_index = (
                    st.session_state.card_index + 1
                ) % total

                st.session_state.show_answer = False

                st.rerun()

        st.write("")

        progress = (st.session_state.card_index + 1) / total

        st.progress(progress)

        st.caption(
            f"📖 Card {st.session_state.card_index + 1} of {total}"
        )

        st.metric(
            "⭐ XP",
            st.session_state.xp
        )
elif page == "❓ Quiz":

    st.title("❓ Quiz")

    if len(st.session_state.quiz) == 0:

        st.warning("Upload notes first.")

    else:

        score = 0

        for i, q in enumerate(st.session_state.quiz):

            st.subheader(f"Question {i+1}")

            st.write(q["question"])

            answer = st.text_input(
                "Answer",
                key=f"quiz{i}"
            )

            if st.button(
                f"Reveal Answer {i+1}",
                key=f"show{i}"
            ):
                add_xp(10)
                st.success(q["answer"])

        st.divider()

        st.info(
            "Complete the quiz before checking the answers."
        )


elif page == "📅 Timetable":

    st.title("📅 Smart Timetable")

    st.caption("Study based on confidence, difficulty and exam dates.")

    count = st.number_input(
        "Number of Subjects",
        1,
        10,
        3
    )

    subjects = []

    for i in range(count):

        st.subheader(f"Subject {i+1}")

        name = st.text_input(
            "Name",
            key=f"name{i}"
        )

        difficulty = st.slider(
            "Difficulty",
            1,
            10,
            5,
            key=f"diff{i}"
        )

        confidence = st.slider(
            "Confidence",
            1,
            10,
            5,
            key=f"conf{i}"
        )

        exam = st.date_input(
            "Exam Date",
            key=f"exam{i}"
        )

        subjects.append(
            {
                "name": name,
                "difficulty": difficulty,
                "confidence": confidence,
                "exam": exam
            }
        )

    hours = st.slider(
        "Study Hours Today",
        1,
        12,
        5
    )

    if st.button("Generate Timetable"):
        add_xp(25)

        today = date.today()

        for s in subjects:

            days = (s["exam"] - today).days

            if days <= 0:
                days = 1

            s["priority"] = (
                s["difficulty"] * 3
                +
                (10 - s["confidence"]) * 2
                +
                (30 / days)
            )

        subjects.sort(
            key=lambda x: x["priority"],
            reverse=True
        )

        total = sum(
            x["priority"]
            for x in subjects
        )

        st.success("Today's Plan")

        start = 8

        for s in subjects:

            study = max(
                1,
                round(hours * s["priority"] / total)
            )

            end = start + study

            st.info(
                f"🕒 {start}:00 - {end}:00 | 📚 {s['name']}"
            )

            start = end

        st.divider()

        nearest = min(
            (x["exam"] - today).days
            for x in subjects
        )

        if nearest <= 2:

            st.error("🚨 PANIC MODE ACTIVATED")

            st.write("🔥 Focus only on the highest priority subjects.")

            top = subjects[:3]

            for subject in top:

                st.success(
                    f"Revise {subject['name']} immediately."
                )

            st.warning("📄 Formula Sheet")

            st.warning("📝 PYQs")

            st.warning("❓ Mock Test")

            st.warning("😴 Sleep before the exam")

        else:

            st.success("🟢 Normal Study Mode")


elif page == "📊 Progress":

    st.title("📊 Progress")

    progress = st.slider(
        "Overall Progress",
        0,
        100,
        st.session_state.progress
    )

    st.session_state.progress = progress

    st.progress(progress / 100)

    if progress < 30:

        st.error("Keep studying!")

    elif progress < 70:

        st.warning("Good progress!")

    else:

        st.success("Excellent! You're almost ready!")

    st.metric(
        "Completion",
        f"{progress}%"
    )

st.sidebar.divider()

st.sidebar.write("StudyPilot AI v2")

st.sidebar.caption(
    datetime.now().strftime("%d %B %Y")
)