import streamlit as st
import pandas as pd
import random
import openai
import time

# --- OpenAI API ---
openai.api_key = "YOUR_OPENAI_API_KEY"  # replace with your key

# --- Page config ---
st.set_page_config(page_title="Smart Exam Coach", layout="wide")

# --- Title ---
st.markdown("<h1 style='color:#2E86C1'>🎯 Smart Exam Coach</h1>", unsafe_allow_html=True)
st.markdown("Upload your mock test once and access all features!")

# --- Sidebar ---
menu = st.sidebar.selectbox(
    "Navigation",
    ["Upload Mock Test", "Weak Topic Analysis", "7-Day Plan", "Progress Dashboard", "Take Quiz", "Flashcards"]
)

# --- Break Reminder ---
if "last_break_time" not in st.session_state:
    st.session_state.last_break_time = time.time()

elapsed = time.time() - st.session_state.last_break_time
if elapsed > 1800:  # 30 min
    with st.container():
        st.warning("⏰ Time for a 5-minute break! Stretch, drink water, relax your eyes.")
        if st.button("I've taken my break"):
            st.session_state.last_break_time = time.time()

# --- HOME PAGE: Upload Mock Test with AI Buddy ---
if menu == "Upload Mock Test":
    col_main, col_ai = st.columns([3,1])

    with col_main:
        st.header("📂 Upload Mock Test CSV")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file)
            st.session_state["mock_test_data"] = data
            st.success("✅ File uploaded successfully!")
            st.dataframe(data)

    with col_ai:
        st.markdown("### 🤖 Ask AI Buddy")
        with st.expander("Click to ask a doubt"):
            question = st.text_area("Type your question here:", height=150)
            if st.button("Submit Doubt"):
                if question.strip() != "":
                    with st.spinner("AI is thinking..."):
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": question}],
                                temperature=0.5,
                                max_tokens=500
                            )
                            answer = response['choices'][0]['message']['content']
                            st.markdown(f"**AI Buddy Answer:** {answer}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please type a question first!")

# --- Stop if no mock test uploaded ---
if menu != "Upload Mock Test" and "mock_test_data" not in st.session_state:
    st.warning("⚠️ Please upload your mock test first!")
    st.stop()

# --- Get uploaded data ---
if "mock_test_data" in st.session_state:
    data = st.session_state["mock_test_data"]

# --- Weak Topic Analysis ---
if menu == "Weak Topic Analysis":
    st.header("📊 Weak Topic Analysis")
    wrong_answers = data[data["Correct"] == False]
    weak_topics = wrong_answers["Topic"].value_counts()
    st.subheader("📝 Your Weak Topics")
    if weak_topics.empty:
        st.success("🎉 Great job! No weak topics found")
    else:
        for topic, count in weak_topics.items():
            st.markdown(f"<div style='padding:10px; margin:5px; border:2px solid #2E86C1;"
                        f"border-radius:10px; background-color:#D6EAF8'>"
                        f"<b>{topic}</b>: {count} mistakes</div>", unsafe_allow_html=True)

# --- 7-Day Revision Plan ---
elif menu == "7-Day Plan":
    st.header("📅 Personalized 7-Day Revision Plan")
    wrong_answers = data[data["Correct"] == False]
    weak_topics = wrong_answers["Topic"].value_counts().index.tolist()

    study_material = {
        "Quadratic Equations": "https://youtu.be/QUADRATIC_VIDEO",
        "Probability": "https://youtu.be/PROBABILITY_VIDEO",
        "Kinematics": "https://youtu.be/KINEMATICS_VIDEO",
        "Current Electricity": "https://youtu.be/ELECTRICITY_VIDEO",
        "Organic Reactions": "https://youtu.be/ORGANIC_REACTIONS_VIDEO"
    }

    if not weak_topics:
        st.success("😎 No weak topics found! Keep revising everything")
    else:
        if "plan_generated" not in st.session_state:
            st.session_state.plan_generated = False
            st.session_state.plan = {}

        if st.button("Generate 7-Day Plan") or st.session_state.plan_generated:
            if not st.session_state.plan_generated:
                # Repeat topics to fill 7 days
                extended_topics = weak_topics.copy()
                while len(extended_topics) < 7:
                    extended_topics += weak_topics
                extended_topics = extended_topics[:7]

                # Assign topics to days
                plan = {}
                for i in range(7):
                    plan[f"Day {i+1}"] = extended_topics[i]

                st.session_state.plan = plan
                st.session_state.plan_generated = True

            # Display plan with cards
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🗓️ 7-Day Plan")
                for d, t in st.session_state.plan.items():
                    st.markdown(f"<div style='padding:10px; margin:5px; border:2px solid #2E86C1;"
                                f"border-radius:10px; background-color:#D6EAF8'>"
                                f"<b>{d}:</b> {t}</div>", unsafe_allow_html=True)
            with col2:
                st.subheader("📚 Study Material")
                for d, t in st.session_state.plan.items():
                    if t in study_material:
                        st.markdown(f"<div style='padding:5px; margin:5px; background-color:#E8F8F5;"
                                    f"border-radius:8px;'>[{t}]({study_material[t]})</div>", unsafe_allow_html=True)

# --- Progress Dashboard ---
elif menu == "Progress Dashboard":
    st.header("📈 Student Progress Dashboard")
    wrong_answers = data[data["Correct"] == False]
    topic_counts = wrong_answers["Topic"].value_counts()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Questions Wrong", len(wrong_answers))
        st.metric("Total Weak Topics", len(topic_counts))
    with col2:
        if not topic_counts.empty:
            st.subheader("📝 Mistakes per Topic")
            st.bar_chart(topic_counts)
        else:
            st.success("No mistakes! Keep it up 😎")

# --- Take Quiz ---
elif menu == "Take Quiz":
    st.header("📝 Weak Topic Quiz")
    weak_topics = data[data["Correct"]==False]["Topic"].unique()
    uploaded_file = st.file_uploader("Upload Quiz CSV (Questions for Weak Topics)", type=["csv"])
    if uploaded_file is not None:
        quiz_data = pd.read_csv(uploaded_file)
        quiz_data = quiz_data[quiz_data["Topic"].isin(weak_topics)]
        score = 0
        for idx, row in quiz_data.iterrows():
            st.markdown(f"<div style='padding:8px; margin:5px; border:1px solid #2E86C1;"
                        f"border-radius:8px; background-color:#F2F3F4'>"
                        f"**Q{idx+1}:** {row['Question']}</div>", unsafe_allow_html=True)
            options = [row['Option1'], row['Option2'], row['Option3'], row['Option4']]
            answer = row['Answer']
            selected = st.radio("Choose an answer:", options, key=idx)
            if st.button("Submit Answer", key=f"btn{idx}"):
                if selected == answer:
                    st.success("✅ Correct!")
                    score += 1
                else:
                    st.error(f"❌ Wrong! Correct answer: {answer}")
        st.subheader(f"Your Total Score: {score}/{len(quiz_data)}")

# --- Flashcards ---
elif menu == "Flashcards":
    st.header("🃏 Flashcards")
    weak_topics = data[data["Correct"]==False]["Topic"].unique()
    uploaded_file = st.file_uploader("Upload Flashcards CSV (Topic, Question, Answer)", type=["csv"])
    if uploaded_file is not None:
        flashcards = pd.read_csv(uploaded_file)
        flashcards = flashcards[flashcards["Topic"].isin(weak_topics)]
        flashcards_list = flashcards.to_dict('records')
        if flashcards_list:
            card_idx = st.slider("Pick a card number", 1, len(flashcards_list), 1)
            card = flashcards_list[card_idx-1]
            st.markdown(f"<div style='padding:8px; margin:5px; border:1px solid #2E86C1;"
                        f"border-radius:8px; background-color:#F2F3F4'><b>Topic:</b> {card['Topic']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding:8px; margin:5px; border:1px solid #2E86C1;"
                        f"border-radius:8px; background-color:#F2F3F4'><b>Question:</b> {card['Question']}</div>", unsafe_allow_html=True)
            if st.button("Show Answer"):
                st.markdown(f"<div style='padding:8px; margin:5px; border:1px solid #2E86C1;"
                            f"border-radius:8px; background-color:#D5F5E3'><b>Answer:</b> {card['Answer']}</div>", unsafe_allow_html=True)
