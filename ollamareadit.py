#!/usr/bin/env python3
import sys
import requests
import subprocess
import textwrap
import re
import os

# Configuration
USER_AGENT = "ollamaread/3.3 (by reddit-user/yourusername)"
MAX_CONTENT_LENGTH = 12000
REQUEST_TIMEOUT = 15

# Set UTF-8 encoding for Windows compatibility
os.environ["PYTHONUTF8"] = "1"

def load_models(filename="models.txt"):
    """Read models from a text file (one per line)."""
    if not os.path.exists(filename):
        print(f"\033[31mError: {filename} not found. Please create it with one model per line.\033[0m")
        sys.exit(1)
    with open(filename, "r", encoding="utf-8") as f:
        models = [line.strip() for line in f if line.strip()]
    if not models:
        print(f"\033[31mError: No models found in {filename}.\033[0m")
        sys.exit(1)
    return models

def choose_model():
    """
    Prompt the user to choose a model from the models.txt file.
    Tab completion is enabled if the readline module is available.
    If a model is passed as the second command-line argument, it is used.
    """
    models = load_models()

    # If a model is provided as a command-line argument, use it.
    if len(sys.argv) >= 3:
        return sys.argv[2]

    try:
        import readline

        def completer(text, state):
            options = [model for model in models if model.startswith(text)]
            if state < len(options):
                return options[state]
            else:
                return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    except ImportError:
        # If readline is not available, proceed without tab completion.
        pass

    print("Available models (from models.txt):")
    for model in models:
        print(f" - {model}")
    model = input("Enter model (press TAB for completion if available): ").strip()
    if model not in models:
        print(f"Warning: '{model}' is not in models.txt. Using it anyway.")
    return model

MODEL_NAME = choose_model()

def display_thread(thread_data):
    """Format and display the original post with styling."""
    title = thread_data.get("title", "No Title")
    author = thread_data.get("author", "[deleted]")
    selftext = re.sub(r'&[#\w]+;', '', thread_data.get("selftext", ""))
    score = thread_data.get("score", 0)
    awards = " ".join(["★"] * len(thread_data.get("all_awardings", [])))

    print("\n\033[1m" + "═" * 80 + "\033[0m")
    print(f"\033[1m{textwrap.fill(title, width=80)}\033[0m")
    print(f"\033[90mPosted by u/{author} | {score} points {awards}\033[0m")
    print("\033[90m" + "─" * 80 + "\033[0m")

    if selftext:
        wrapped_text = textwrap.fill(selftext, width=80, replace_whitespace=False)
        print(f"\n{wrapped_text}\n")
    else:
        print("\n\033[3m[Link post - no text content]\033[0m\n")
    print("\033[90m" + "─" * 80 + "\033[0m")

def display_comment(comment, indent=0):
    """Format and display a single comment with threading visualization."""
    data = comment.get("data", {})
    body = re.sub(r'&[#\w]+;', '', data.get("body", ""))
    author = data.get("author") or "[deleted]"
    score = data.get("score", "?")

    if not body:
        return

    if indent > 0:
        print("│ " * (indent // 2 - 1) + "├─ ", end="")

    wrapped = textwrap.fill(
        body,
        width=80 - indent,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent
    )
    print(f"\033[33mu/{author} ({score} points):\033[0m")
    print(f"{wrapped}\n")

    replies = data.get("replies", {})
    children = []
    if isinstance(replies, dict):
        children = replies.get("data", {}).get("children", [])
    elif isinstance(replies, list):
        children = replies

    for reply in children:
        if isinstance(reply, dict) and reply.get("kind") == "t1":
            display_comment(reply, indent + 2)

def fetch_reddit_data(url):
    """Fetch and validate Reddit JSON data from the given URL."""
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"\033[31mError: {str(e)}\033[0m")
        sys.exit(1)

def generate_summary(post_data, comments_data):
    """Generate an in-depth summary using Ollama with the provided prompt."""
    post_content = f"Original Post:\nTitle: {post_data.get('title', '')}\n{post_data.get('selftext', '')}\n\n"
    comments_content = "\n".join(
        c["data"].get("body", "")
        for c in comments_data
        if c.get("kind") == "t1" and "body" in c.get("data", {})
    )
    full_content = f"{post_content}Comments:\n{comments_content}"[:MAX_CONTENT_LENGTH]

    prompt = f"""# Reddit Thread In-Depth Analysis

**1. Original Post Overview:**  
- Provide a concise summary of the original post, capturing its central topic, key points, or underlying perspective, along with any necessary background context.

**2. Key Discussion Themes:**  
- Identify 3-5 central discussion points from the comments.  
- Present both supporting and opposing perspectives to capture the full scope of the conversation.

**3. Controversial/Divisive Opinions:**  
- Highlight areas where opinions are notably divided or contentious.  
- Explain any underlying reasons for these splits if evident.

**4. Data, Statistics, and Notable Quotations:**  
- Extract important statistics, data points, or impactful quotations.  
- Ensure attributions are included when available.

**5. Overall Community Sentiment:**  
- Summarize the overall tone and sentiment of the discussion (e.g., positive, negative, mixed).

**Formatting Requirements:**  
- Use markdown with clear, descriptive section headers.  
- Be both concise and comprehensive in your analysis.

Thread content:
{full_content}
"""

    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=300,
            env=os.environ.copy()
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Summary generation timed out after 5 minutes"
    except Exception as e:
        stderr_text = ""
        if hasattr(e, 'stderr') and e.stderr:
            try:
                stderr_text = e.stderr.decode('utf-8', errors='replace')
            except Exception:
                stderr_text = str(e.stderr)
        return f"Summary error: {str(e)}\nSTDERR: {stderr_text}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python ollamaread.py <reddit-url> [model]")
        sys.exit(1)

    # Prepare the Reddit JSON URL.
    base_url = sys.argv[1].split("?")[0].rstrip("/")
    json_url = f"{base_url}.json"

    try:
        json_data = fetch_reddit_data(json_url)
        post_data = json_data[0]["data"]["children"][0]["data"]
        comments_data = json_data[1]["data"]["children"]
    except (KeyError, IndexError) as e:
        print(f"\033[31mError parsing Reddit data: {str(e)}\033[0m")
        sys.exit(1)

    # Display the original post.
    display_thread(post_data)

    # Display the comments.
    print("\033[1mCOMMENTS:\033[0m\n")
    for comment in comments_data:
        if comment.get("kind") == "t1":
            display_comment(comment)
    print("\033[90m" + "═" * 80 + "\033[0m\n")

    # Generate and display the analytical summary.
    print(f"\033[1mANALYTICAL SUMMARY (Model: {MODEL_NAME})".center(80) + "\033[0m")
    summary = generate_summary(post_data, comments_data)
    print(summary)

if __name__ == "__main__":
    main()
