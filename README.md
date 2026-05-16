# AI Toolkit

## Overview

A collection of AI-powered developer tools and applications demonstrating practical integrations of large language models, machine learning, and automation. The toolkit includes three independent projects:

- **Auto PR Review** — An AI-assisted code reviewer for git diffs using Google Gemini, paired with a sample Flask Todo API for testing.
- **Log Anomaly Detector** — A Streamlit dashboard that combines Isolation Forest anomaly detection with local LLM-powered root cause analysis.
- **README Auto-Generator** — A CLI tool that scans any repository and generates a professional README using Anthropic Claude.

Each project is self-contained and showcases a different facet of applied AI engineering: code review automation, hybrid statistical + LLM analysis, and content generation from source.

## Features

### Auto PR Review
- REST API for Todo management (`GET`, `POST`, `DELETE`)
- AI-powered git diff review via Gemini 2.0 Flash
- Automatic retries with backoff for rate-limited requests
- Diff truncation to respect model context limits
- Pytest test suite

### Log Anomaly Detector
- HDFS log parsing with regex-based extraction
- Feature engineering (error level, message length, component frequency, PID normalization)
- Isolation Forest anomaly detection with configurable sensitivity
- Local LLM explanations via Ollama (zero cost, fully private)
- Interactive Streamlit dashboard with Plotly visualizations
- Tabbed analysis views: distribution, components, timeline

### README Auto-Generator
- Git-aware repository walking (respects `.gitignore`)
- Smart file prioritization (entry points and configs first)
- Configurable context budget for large repos
- Multi-language support (Python, JS/TS, Go, Rust, Java, etc.)
- Claude Opus-powered README generation

## Installation

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.ai) (for the log anomaly detector's LLM features)
- API keys: `ANTHROPIC_API_KEY` (README generator), `GEMINI_API_KEY` (PR review)

### Setup

Clone the repository:

```bash
git clone <repository-url>
cd <repository-root>
```

Install dependencies per project:

```bash
# Auto PR Review
pip install -r AI/Auto_PR_review/app/requirements.txt

# Log Anomaly Detector
pip install -r AI/log-anomaly-detector/requirements.txt

# README Auto-Generator
pip install anthropic python-dotenv
```

Configure API keys in a `.env` file or environment:

```bash
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

For the log anomaly detector, pull the local LLM:

```bash
ollama pull llama3.2:3b
```

## Usage

### Auto PR Review

Run the Todo API:

```bash
cd AI/Auto_PR_review/app
python app.py
```

Run the AI reviewer on a git diff:

```bash
git diff main | python AI/Auto_PR_review/scripts/ai_review.py
```

Run tests:

```bash
cd AI/Auto_PR_review/app
pytest test_app.py
```

### Log Anomaly Detector

Launch the dashboard:

```bash
cd AI/log-anomaly-detector
streamlit run app.py
```

Upload a `.log` or `.txt` file via the sidebar, or use the bundled HDFS sample. Tune sensitivity and AI explanation count, then review detected anomalies with auto-generated SRE-style root cause analysis.

### README Auto-Generator

Generate a README for any repository:

```bash
python "AI/README auto-generator/generate.py" /path/to/your/repo
```

The output is saved to `README.generated.md` inside the target repo.

## Examples

### Adding a Todo via the API

```bash
curl -X POST http://localhost:5000/todos \
  -H "Content-Type: application/json" \
  -d '{"task": "Write documentation"}'
```

Response:

```json
{ "id": 1, "task": "Write documentation", "done": false }
```

### AI Code Review Output

```bash
$ git diff HEAD~1 | python scripts/ai_review.py

- Missing input validation: `data["task"]` will raise KeyError if absent.
- In-memory `todos` list will not persist across restarts.
- No security concerns in this diff.
```

### Log Anomaly Explanation

After the detector flags a log entry, the LLM produces:

```
1. Summary: A DataNode reported a block replication failure during a write operation.
2. Probable cause: Network partition between the NameNode and the target DataNode,
   or the DataNode running out of disk space.
3. Diagnostic: Run `hdfs dfsadmin -report` to inspect DataNode health and capacity.
```

### Generated README Snippet

```bash
$ python generate.py ~/projects/my-app
📂 Walking repo at /home/user/projects/my-app...
   Using git to list files (respecting .gitignore).
   Found 47 relevant files.
   Including 47 files in prompt (84,231 chars). Skipped 0 to fit budget.
🤖 Calling Claude...
✅ Saved to /home/user/projects/my-app/README.generated.md
```

## Project Structure

```
.
├── AI/
│   ├── Auto_PR_review/
│   │   ├── app/
│   │   │   ├── app.py              # Flask Todo API
│   │   │   ├── test_app.py         # Pytest suite
│   │   │   └── requirements.txt
│   │   └── scripts/
│   │       └── ai_review.py        # Gemini-powered diff reviewer
│   │
│   ├── log-anomaly-detector/
│   │   ├── app.py                  # Streamlit dashboard
│   │   ├── parser.py               # HDFS log parser
│   │   ├── features.py             # Feature engineering
│   │   ├── detector.py             # Isolation Forest detector
│   │   ├── explainer.py            # Ollama LLM integration
│   │   ├── test_parser.py
│   │   └── requirements.txt
│   │
│   └── README auto-generator/
│       └── generate.py             # Claude-powered README generator
│
└── README.md
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
