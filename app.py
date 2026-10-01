import json
from datetime import datetime
from pathlib import Path

import streamlit as st
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Text Summarizer",
    page_icon="📝",
    layout="wide"
)


# ============================================================
# GROQ API KEY
# ============================================================

GROQ_API_KEY = "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"


# ============================================================
# FILE PATH
# ============================================================

DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "history.json"

DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# JSON FUNCTIONS
# ============================================================

def load_history():
    """Load history from JSON."""

    if not HISTORY_FILE.exists():
        save_history([])
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_history(history):
    """Save history to JSON."""

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            indent=4,
            ensure_ascii=False
        )


def add_history(original_text, summary, length):
    """Add a summary to history."""

    history = load_history()

    new_item = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "length": length,
        "original_text": original_text,
        "summary": summary
    }

    history.insert(0, new_item)

    # Keep latest 20 summaries
    history = history[:20]

    save_history(history)


def delete_history(item_id):
    """Delete one history item."""

    history = load_history()

    history = [
        item for item in history
        if item.get("id") != item_id
    ]

    save_history(history)


def clear_history():
    """Clear all history."""

    save_history([])


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def count_words(text):
    """Count words."""

    return len(text.split())


def calculate_compression(original, summary):
    """Calculate compression percentage."""

    original_count = count_words(original)
    summary_count = count_words(summary)

    if original_count == 0:
        return 0

    result = (
        (original_count - summary_count)
        / original_count
    ) * 100

    return max(0, round(result, 1))


# ============================================================
# GROQ SUMMARIZATION
# ============================================================

def generate_summary(text, summary_length):

    if not GROQ_API_KEY or \
       GROQ_API_KEY == "PASTE_YOUR_GROQ_API_KEY_HERE":

        raise ValueError(
            "Please add your Groq API key in app.py."
        )

    client = Groq(
        api_key=GROQ_API_KEY
    )

    instructions = {

        "Short": """
Create a very short summary.
Keep only the most important points.
Use approximately 20-25% of the original information.
""",

        "Medium": """
Create a balanced summary.
Include the main ideas and important supporting details.
Do not include unnecessary information.
""",

        "Detailed": """
Create a detailed summary.
Include the major ideas, important facts,
supporting details, and conclusions.
"""
    }

    prompt = f"""
You are an expert AI text summarization assistant.

{instructions[summary_length]}

Follow these rules:

1. Do not invent information.
2. Do not change the meaning of the original text.
3. Use clear and simple language.
4. Remove unnecessary repetition.
5. Keep important facts and concepts.
6. Return only the summary.
7. Do not say "Here is the summary".

TEXT:

{text}
"""

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise and reliable "
                    "text summarization assistant."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.2,

        max_tokens=2048
    )

    return response.choices[0].message.content.strip()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #777;
        margin-bottom: 30px;
    }

    .stat-box {
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }

    .stat-number {
        font-size: 26px;
        font-weight: bold;
    }

    .stat-label {
        color: #777;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '📝 AI Text Summarizer'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Summarize your text using Groq AI'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    summary_length = st.selectbox(
        "Summary Length",
        [
            "Short",
            "Medium",
            "Detailed"
        ],
        index=1
    )

    st.divider()

    history = load_history()

    st.header("📚 History")

    st.write(
        f"Saved summaries: **{len(history)}**"
    )

    if history:

        if st.button(
            "🗑️ Clear All History",
            use_container_width=True
        ):

            clear_history()

            st.session_state.pop(
                "summary",
                None
            )

            st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

left_column, right_column = st.columns(
    2
)


# ============================================================
# INPUT
# ============================================================

with left_column:

    st.subheader("📄 Input Text")

    uploaded_file = st.file_uploader(
        "Upload a TXT file",
        type=["txt"]
    )

    uploaded_text = ""

    if uploaded_file:

        try:

            uploaded_text = uploaded_file.read().decode(
                "utf-8"
            )

            st.success(
                f"Loaded: {uploaded_file.name}"
            )

        except UnicodeDecodeError:

            st.error(
                "Could not read the file. "
                "Please use a UTF-8 TXT file."
            )

    text = st.text_area(
        "Enter your text",
        value=uploaded_text,
        height=400,
        placeholder=(
            "Paste your article, notes, "
            "research paper or any text here..."
        ),
        label_visibility="collapsed"
    )

    original_words = count_words(text)

    st.caption(
        f"📊 Words: **{original_words}**"
    )

    summarize = st.button(
        "✨ Generate Summary",
        type="primary",
        use_container_width=True
    )


# ============================================================
# OUTPUT
# ============================================================

with right_column:

    st.subheader("✨ Summary")

    if summarize:

        if not text.strip():

            st.warning(
                "Please enter some text first."
            )

        elif original_words < 10:

            st.warning(
                "Please enter at least 10 words."
            )

        else:

            with st.spinner(
                "🤖 Groq AI is summarizing..."
            ):

                try:

                    summary = generate_summary(
                        text,
                        summary_length
                    )

                    st.session_state["summary"] = summary
                    st.session_state[
                        "original_text"
                    ] = text

                    add_history(
                        text,
                        summary,
                        summary_length
                    )

                except Exception as error:

                    st.error(
                        f"❌ Error: {error}"
                    )


    # Show summary
    if "summary" in st.session_state:

        summary = st.session_state["summary"]

        original_text = st.session_state.get(
            "original_text",
            text
        )

        st.text_area(
            "Generated Summary",
            value=summary,
            height=350
        )

        summary_words = count_words(
            summary
        )

        compression = calculate_compression(
            original_text,
            summary
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {count_words(original_text)}
                    </div>
                    <div class="stat-label">
                        Original Words
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {summary_words}
                    </div>
                    <div class="stat-label">
                        Summary Words
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {compression}%
                    </div>
                    <div class="stat-label">
                        Compression
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.download_button(
            "⬇️ Download Summary",
            data=summary,
            file_name="summary.txt",
            mime="text/plain",
            use_container_width=True
        )


# ============================================================
# CLEAR CURRENT SUMMARY
# ============================================================

st.divider()

if st.button(
    "🧹 Clear Current Summary",
    use_container_width=True
):

    st.session_state.pop(
        "summary",
        None
    )

    st.session_state.pop(
        "original_text",
        None
    )

    st.rerun()


# ============================================================
# HISTORY
# ============================================================

st.divider()

st.subheader("📚 Summary History")

history = load_history()

if not history:

    st.info(
        "No summaries yet."
    )

else:

    for item in history:

        with st.expander(
            f"📄 {item['date']} — "
            f"{item['length']}"
        ):

            st.markdown(
                "**Original Text:**"
            )

            original = item[
                "original_text"
            ]

            st.write(
                original[:500]
                + (
                    "..."
                    if len(original) > 500
                    else ""
                )
            )

            st.markdown(
                "**Summary:**"
            )

            st.write(
                item["summary"]
            )

            col1, col2 = st.columns(2)

            with col1:

                st.download_button(
                    "⬇️ Download",
                    data=item["summary"],
                    file_name=(
                        f"summary_{item['id']}.txt"
                    ),
                    mime="text/plain",
                    key=f"download_{item['id']}",
                    use_container_width=True
                )

            with col2:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{item['id']}",
                    use_container_width=True
                ):

                    delete_history(
                        item["id"]
                    )

                    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🤖 Powered by Groq AI • "
    "Python + Streamlit + JSON"
)