import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re # For cleaning text

load_dotenv() # Load environment variables

# --- Initialize Gemini API ---
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")
    genai.configure(api_key=gemini_api_key)
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to configure Gemini API. Ensure GEMINI_API_KEY is correct in .env. Details: {e}")
    gemini_api_key = None 

# Use a suitable Gemini model for contextual analysis
# 'gemini-1.5-flash' is good for speed, 'gemini-pro' for potentially deeper reasoning.
text_model = genai.GenerativeModel('gemini-1.5-flash') 

def _fetch_text_from_url(url: str) -> str:
    """Fetches and extracts main text content from a given URL."""
    try:
        response = requests.get(url, timeout=10) # 10-second timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find main content sections
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])

        # Basic cleaning
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit text to avoid excessively long inputs for Gemini
        return text[:20000] # Limit to ~20k characters for robust processing

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch content from URL: {e}. Check URL or network.")
    except Exception as e:
        raise Exception(f"Failed to parse content from URL: {e}.")

def analyze_for_disinformation(content_text: str, analysis_type: str = "Contextual Analysis") -> str:
    """
    Analyzes content for disinformation, bias, or factual inconsistencies using Gemini.

    Args:
        content_text (str): The news article text or social media post to analyze.
        analysis_type (str): The specific type of analysis requested (e.g., "Contextual Analysis", "Bias Detection", "Factual Consistency").

    Returns:
        str: Gemini's detailed analysis report.
    """
    if not gemini_api_key:
        return "ERROR: Gemini API Key is not configured. Please check your .env file."
        
    if not content_text.strip():
        return "Please provide text content for analysis."

    # Limit input for Gemini, especially for very long articles
    truncated_content = content_text[:15000] # Adjust based on token limits

    prompt = f"""
    You are an expert AI assistant specialized in analyzing news and social media content for disinformation, bias, and factual inconsistencies. Your goal is to provide a comprehensive and unbiased "{analysis_type}" report on the provided text.

    **Focus on the following aspects for your analysis:**
    - **Factual Consistency:** Are claims supported by evidence? Any logical fallacies?
    - **Source Credibility (if implied/known):** Does the text use reliable sources? (If URL provided, assume standard news unless otherwise evident).
    - **Tone and Language:** Is it sensationalist, inflammatory, or emotionally manipulative?
    - **Omissions/Context:** Is crucial context missing? Are facts presented selectively?
    - **Logical Coherence:** Does the argument make sense?

    Here is the content to analyze:
    ---
    {truncated_content}
    ---

    Please provide a detailed report for "{analysis_type}" based on the content above. Summarize your findings, highlight specific examples where possible, and provide a conclusion on the likelihood of disinformation or bias.
    """

    try:
        response = text_model.generate_content(prompt)
        return response.text
    except Exception as e:
        if "quota" in str(e).lower() or "rate limit" in str(e).lower():
            return f"API Error: You might have hit a rate limit or quota. Please try again later. Details: {e}"
        if "authentication" in str(e).lower() or "api key" in str(e).lower() or "unauthorized" in str(e).lower():
            return f"API Error: Invalid or missing API Key. Please double-check your .env file or deployment secrets. Details: {e}"
        if "content_filter" in str(e).lower() or "safety" in str(e).lower():
            return f"API Error: Content may violate safety guidelines. Please try different content or rephrase your request. Details: {e}"
        if "tokens" in str(e).lower() and "exceeded" in str(e).lower():
            return f"API Error: Input text is too long for analysis. Please try a shorter article or summary. Details: {e}"
        return f"An unexpected error occurred during AI analysis: {e}. Please try again."

# Example Usage (typically run via app.py)
if __name__ == "__main__":
    print("This module defines the core AI disinformation detection logic.")
    print("To test, you should run app.py.")
    # Example test (requires internet for URL fetch)
    # try:
    #     test_url = "https://www.bbc.com/news/world-asia-62228387" # A factual news article
    #     text = _fetch_text_from_url(test_url)
    #     print(f"Fetched {len(text)} characters from URL.")
    #     analysis = analyze_for_disinformation(text, "Factual Consistency Check")
    #     print("\n--- Analysis Report ---")
    #     print(analysis)
    # except Exception as e:
    #     print(f"Test failed: {e}")