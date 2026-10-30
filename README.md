# School of AI Curriculum Assistant

An educational Streamlit application that answers curriculum questions using keyword-based retrieval and the Gemini API.

## Run locally

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export GEMINI_API_KEY="your-new-key"
streamlit run app.py
```

Run from the repository root so `syllabus_text.txt` can be found. Use your own valid API key; provider usage limits and charges may apply. Never commit credentials.

## How it works

`app.py` splits the supplied syllabus into course chunks, retrieves keyword matches, and includes that context in a model request. The Streamlit interface maintains conversation history. `gemini_test.py` is an earlier API/UI experiment; `key.txt` contains legacy Python source, not an application configuration file.

## Current limitations

- Retrieval uses keywords, not embeddings or a vector database.
- Context is retrieved for the first message of a conversation; follow-up retrieval needs improvement.
- The context budget is measured in characters despite the variable name `max_tokens`.
- Generated answers and institutional information require verification against current official sources.
- No retrieval-quality benchmark or automated regression suite is included yet.

## Credential hygiene

An API key was previously committed in `app.py`. It has been removed from the current code, but remains in older Git history. The owner must revoke/rotate that exposed key with the provider before using this project. Removing a file or commit does not revoke a credential.
