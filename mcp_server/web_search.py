import requests
import json
import re
import uuid


def _generate_unique_id():
    """Generate a unique UUID."""
    return str(uuid.uuid4())


def _extract_clean_answer(response_text: str) -> str:
    """Clean up markdown and other artifacts from the response."""
    if not response_text:
        return ""

    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', response_text)  # bold
    cleaned = re.sub(r'\*\s+', '• ', cleaned)  # bullets
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # extra newlines
    cleaned = re.sub(r'\[[\d\s,]+\]', '', cleaned)  # citations
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', '', cleaned)  # markdown links

    return cleaned.strip()


def _make_api_request(query: str) -> str:
    """Send a request to the local API and stream the best possible answer."""
    payload = {
        "input": {
            "messages": [
                {
                    "type": "human",
                    "content": query,
                    "id": _generate_unique_id()
                }
            ],
            "initial_search_query_count": 3,
            "max_research_loops": 3,
            "reasoning_model": "gemini-2.5-flash-preview-04-17"
        },
        "stream_mode": ["messages-tuple", "values", "updates"],
        "assistant_id": "agent",
        "on_disconnect": "cancel"
    }

    try:
        # Step 1: Get thread ID
        resp = requests.post("http://localhost:2024/threads/", json=payload)
        resp.raise_for_status()
        thread_id = resp.json().get("thread_id")

        if not thread_id:
            return ""

        # Step 2: Stream the response
        stream_url = f"http://localhost:2024/threads/{thread_id}/runs/stream"
        final_answer = ""

        with requests.post(stream_url, json=payload, stream=True) as stream_resp:
            stream_resp.raise_for_status()
            for line in stream_resp.iter_lines(decode_unicode=True):
                if not line or line.startswith(":"):
                    continue

                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        parsed = json.loads(data_str)

                        # Priority order: web_research_result > messages > content > other long text fields
                        if isinstance(parsed, dict):
                            if isinstance(parsed.get("web_research_result"), str) and len(parsed["web_research_result"]) > len(final_answer):
                                final_answer = parsed["web_research_result"]

                            if "messages" in parsed:
                                for msg in parsed["messages"]:
                                    content = msg.get("content", "")
                                    if isinstance(content, str) and len(content) > len(final_answer):
                                        final_answer = content

                            if isinstance(parsed.get("content"), str) and len(parsed["content"]) > len(final_answer):
                                final_answer = parsed["content"]

                            for key, value in parsed.items():
                                if key not in ["messages", "content", "web_research_result"] and isinstance(value, str) and len(value) > 50:
                                    if len(value) > len(final_answer):
                                        final_answer = value

                    except json.JSONDecodeError:
                        if len(data_str) > len(final_answer):
                            final_answer = data_str

        return final_answer.strip()

    except requests.RequestException as req_err:
        print(f"[ERROR] API request failed: {req_err}")
        return ""
    except Exception as err:
        print(f"[ERROR] Unexpected error: {err}")
        return ""


def get_web_summary(query: str) -> str:
    """
    Main callable function.
    Accepts a question/query and returns the cleaned final answer (string).
    """
    if not query:
        return "Query is empty."

    raw_answer = _make_api_request(query)
    clean_answer = _extract_clean_answer(raw_answer)

    return clean_answer if clean_answer else "No answer received."
