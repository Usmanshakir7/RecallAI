
import streamlit as st
import requests

st.set_page_config(
    page_title="RecallAI",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 RecallAI")
st.caption("Every conversation. Every insight. One place.")
st.write("Turn meeting transcripts into searchable knowledge.")

API_URL = "http://127.0.0.1:8000/analyze"

transcript = st.text_area(
    "Meeting Transcript",
    placeholder="Paste your meeting or lecture transcript here...",
    height=220,
)

if st.button("✨ Process Transcript", type="primary"):
    if not transcript.strip():
        st.warning("Please enter a transcript first.")

    else:
        with st.spinner("Processing transcript..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"transcript": transcript},
                    timeout=120,
                )

                response.raise_for_status()
                result = response.json()

                st.success("Transcript processed successfully!")

                st.subheader("📝 Summary")
                st.write(result.get("summary", "No summary returned."))

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📌 Key Topics")
                    st.write(result.get("topics", []))

                    st.subheader("💡 Important Points")
                    st.write(result.get("key_points", []))

                with col2:
                    st.subheader("✅ Decisions")
                    st.write(result.get("decisions", []))

                    st.subheader("📋 Action Items")
                    st.write(result.get("action_items", []))

            except requests.exceptions.ConnectionError:
                st.error(
                    "Backend is not running or cannot be reached. "
                    "Please start the FastAPI backend."
                )

            except requests.exceptions.Timeout:
                st.error("Processing took too long. Please try again.")

            except requests.exceptions.RequestException as error:
                st.error(f"Backend request failed: {error}")

            except ValueError:
                st.error("Backend returned an invalid JSON response.")
