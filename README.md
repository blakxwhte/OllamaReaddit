# OllamaReddit

**OllamaReddit** is a command-line Python tool that fetches Reddit threads, displays the original post and its comments with clear formatting, and then generates an in-depth Markdown analysis using the Ollama CLI. This tool leverages your locally installed Ollama models to summarize discussions, helping you quickly grasp key themes, opinions, and data points from Reddit threads.

## Features

- **Reddit Thread Fetching:**  
  Retrieves data (original post and comments) from Reddit threads via the Reddit JSON API.

- **Formatted Display:**  
  Nicely formats and prints the thread using ANSI colors and indentation for nested comments.

- **In-Depth Analysis:**  
  Constructs a detailed prompt for Ollama, which then generates an analytical summary covering:
  - Original post overview
  - Key discussion themes (with supporting and opposing views)
  - Controversial or divisive opinions
  - Data points, statistics, and notable quotations
  - Overall community sentiment

- **Interactive Model Selection:**  
  Loads available Ollama models from a local `models.txt` file and offers an interactive prompt with tab-completion (using Python’s `readline` module) to select a model.

## Prerequisites

- **Python 3.6+**
- **Ollama CLI:**  
  Make sure the [Ollama CLI](https://ollama.ai/) is installed and available in your system's PATH.

- **Python Packages:**  
  Install required packages via `pip` (see [Requirements](#requirements) below).

## Requirements

A `requirements.txt` file is provided for easy dependency installation:

```txt
requests
pyreadline3; platform_system=="Windows"
