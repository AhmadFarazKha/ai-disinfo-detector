import streamlit as st
import os
from src.core.disinfo_detector import analyze_for_disinformation, _fetch_text_from_url
from src.utils.file_handler import create_directories_if_not_exist
from dotenv import load_dotenv

# Ensure data directory exists (for consistency)
create_directories_if_not_exist("data")

# Load environment variables early
load_dotenv()

# --- Streamlit Session State Initialization ---
if 'input_type' not in st.session_state:
    st.session_state.input_type = "text"
if 'text_input_content' not in st.session_state:
    st.session_state.text_input_content = ""
if 'url_input_content' not in st.session_state:
    st.session_state.url_input_content = ""
if 'selected_analysis_type' not in st.session_state:
    st.session_state.selected_analysis_type = "Contextual Analysis"
if 'analysis_report' not in st.session_state:
    st.session_state.analysis_report = ""
if 'show_report' not in st.session_state:
    st.session_state.show_report = False

# --- Page Configuration (Theme controlled by .streamlit/config.toml) ---
st.set_page_config(
    page_title="AI Disinformation Detector",
    page_icon="🚫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- NO CUSTOM CSS IN THIS VERSION ---
# This version removes all custom CSS from app.py to guarantee no CSS code appears on the page.
# Styling will rely solely on .streamlit/config.toml for background, primary color, text color, etc.

# --- Application Content ---
st.title("🚫 AI Disinformation Detector")
st.markdown("<p style='text-align: center; font-size: 1.1rem; margin-bottom: 2rem;'>Analyze news articles or social media posts for potential disinformation, bias, or factual inconsistencies.</p>", unsafe_allow_html=True)

col_main_l, col_main_center, col_main_r = st.columns([1, 4, 1])

with col_main_center:
    st.info("⚠️ Disclaimer: This AI tool provides analytical insights and is not a definitive arbiter of truth. Always verify information from multiple reliable sources.")
    
    st.markdown("### 1. Provide Content for Analysis")
    input_source_cols = st.columns(2)
    with input_source_cols[0]:
        if st.button("Enter Text Directly 📝", use_container_width=True, key="btn_input_text"):
            st.session_state.input_type = "text"
            st.session_state.analysis_report = ""
            st.session_state.show_report = False
            st.rerun()
    with input_source_cols[1]:
        if st.button("Fetch from URL 🌐", use_container_width=True, key="btn_input_url"):
            st.session_state.input_type = "url"
            st.session_state.analysis_report = ""
            st.session_state.show_report = False
            st.rerun()

    if st.session_state.input_type == "text":
        st.session_state.text_input_content = st.text_area(
            "Paste your news article text or social media post here:",
            value=st.session_state.text_input_content,
            placeholder="e.g., 'Recent reports claim ...' or a full article body.",
            height=250,
            key="text_input_area"
        )
        content_to_analyze = st.session_state.text_input_content
    else: # input_type == "url"
        st.session_state.url_input_content = st.text_input(
            "Enter the URL of the news article or post:",
            value=st.session_state.url_input_content,
            placeholder="e.g., https://www.bbc.com/news/world-asia-62228387",
            key="url_input_field"
        )
        content_to_analyze = st.session_state.url_input_content

    st.markdown("---")

    st.markdown("### 2. Select Analysis Type & Analyze")
    analysis_options = [
        "Contextual Analysis",
        "Bias Detection",
        "Factual Consistency Check",
        "Sensationalism/Tone Analysis"
    ]
    st.session_state.selected_analysis_type = st.selectbox(
        "Choose the type of disinformation analysis:",
        options=analysis_options,
        index=analysis_options.index(st.session_state.selected_analysis_type) if st.session_state.selected_analysis_type in analysis_options else 0,
        key="analysis_type_selector"
    )

    col_btn_analyze, col_btn_clear = st.columns(2)
    with col_btn_analyze:
        if st.button("Analyze Content with AI 🧠", use_container_width=True, key="btn_analyze_content"):
            if not content_to_analyze.strip():
                st.warning("Please provide content (text or URL) for analysis.")
                st.session_state.show_report = False
                st.stop()
            
            final_content_for_ai = content_to_analyze
            if st.session_state.input_type == "url":
                with st.spinner("Fetching content from URL..."):
                    try:
                        final_content_for_ai = _fetch_text_from_url(st.session_state.url_input_content)
                        if not final_content_for_ai.strip():
                            st.error("Failed to extract readable text from the provided URL. It might be behind a paywall or an image-only site.") # More specific error message
                            st.session_state.show_report = False
                            st.stop()
                        st.info("Content fetched from URL successfully.")
                    except Exception as e:
                        st.error(f"Error fetching/parsing URL content: {e}. Please ensure it's a valid, publicly accessible URL.")
                        st.session_state.show_report = False
                        st.stop()

            with st.spinner("AI is performing analysis for disinformation..."):
                try:
                    analysis_output = analyze_for_disinformation(
                        final_content_for_ai,
                        st.session_state.selected_analysis_type
                    )
                    st.session_state.analysis_report = analysis_output
                    st.session_state.show_report = True
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Error during AI analysis: {e}. Please ensure your API key is correct and content is appropriate/not too long.")
                    st.session_state.show_report = False

    with col_btn_clear:
        if st.button("Clear All 🗑️", use_container_width=True, key="btn_clear_all"):
            st.session_state.input_type = "text"
            st.session_state.text_input_content = ""
            st.session_state.url_input_content = ""
            st.session_state.selected_analysis_type = "Contextual Analysis"
            st.session_state.analysis_report = ""
            st.session_state.show_report = False
            st.info("All cleared! Ready for new content.")
            st.rerun()

# Display Analysis Result
if st.session_state.show_report and st.session_state.analysis_report:
    with col_main_center:
        st.markdown("---")
        st.subheader("💡 AI Analysis Report:")
        st.markdown(st.session_state.analysis_report)

        st.download_button(
            label="Download Analysis Report ⬇️",
            data=st.session_state.analysis_report.encode('utf-8'),
            file_name="disinformation_analysis.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_download_report"
        )
    
st.markdown("---")
st.info("Powered by Google Gemini AI and Streamlit.")
st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #a0a0a0; margin-top: 2rem;'>Developed with ❤️ in Essa Khel, Punjab, Pakistan</p>", unsafe_allow_html=True)