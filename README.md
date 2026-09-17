# AI Pulse Curator

Automated Weekly YouTube AI Trend Discovery, Video Quality Scoring, and Training Curriculum Synchronization.

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![API](https://img.shields.io/badge/YouTube%20Data%20API-v3-FF0000.svg?logo=youtube&logoColor=white)](https://developers.google.com/youtube/v3)
[![Data Engine](https://img.shields.io/badge/Data%20Engine-Pandas%20%7C%20OpenPyXL-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
  - [Stage 1: Trend & Topic Discovery](#stage-1-trend--topic-discovery)
  - [Stage 2: Video Quality Curation](#stage-2-video-quality-curation)
- [Directory Structure](#directory-structure)
- [Installation & Setup](#installation--setup)
- [YouTube Data API v3 Setup](#youtube-data-api-v3-setup)
- [Execution Guide](#execution-guide)
  - [Step 1: Trend Analyzer](#step-1-trend-analyzer)
  - [Step 2: Video Curator](#step-2-video-curator)
- [Spreadsheet Schema](#spreadsheet-schema)
- [Edge Cases & Error Handling](#edge-cases--error-handling)
- [License](#license)

---

## Overview

Managing an organizational AI training curriculum manually every month creates bottlenecks:
- Rapid advancements in AI models and tools are easily missed.
- Manual searches result in noise and clickbait.
- Logging dates, formatting URLs, and maintaining index counters is tedious.

**AI Pulse Curator** solves this with an automated two-stage weekly pipeline:
1. **Trend Analyzer (`step1_trend_analyzer.py`):** Ingests existing topics from `Training.xlsx`, scans recent YouTube uploads across AI domains, and calculates keyword and hashtag velocity to identify what is booming.
2. **Video Curator (`step2_video_curator.py`):** Evaluates candidate videos using an engagement-to-view scoring model and appends the top-rated educational videos directly into your training spreadsheet.

---

```markdown
## System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                 Historical Training.xlsx                    │
│           (Existing Topics, Schema, Last Sr No)             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: step1_trend_analyzer.py                            │
│                                                             │
│  [YouTube API v3] ──► [NLP Tokenizer] ──► [Weighting Engine]│
│                                                   │         │
│                                                   ▼         │
│                                       booming_trends.json   │
│                                       • Booming Keywords    │
│                                       • Booming Hashtags    │
│                                       • Booming Topics      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: step2_video_curator.py                             │
│                                                             │
│  [Booming Topics] ──► [Deep Search] ──► [Scoring Algorithm] │
│                                                   │         │
│                                                   ▼         │
│                                      [Excel Data Appender]  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Updated Training.xlsx                     │
│         • Continuous sequential Sr No                       │
│         • Chronological incrementing dates                  │
│         • Formatted clickable hyperlinks                    │
└─────────────────────────────────────────────────────────────┘


## How It Works

### Stage 1: Trend & Topic Discovery
- Ingests past topics from `Training.xlsx` to understand your historical curriculum.
- Fetches videos published over the last 14 to 15 days matching AI search queries.
- Cleans and normalizes text, stripping punctuation and common filler words (`tutorial`, `guide`, `beginner`, etc.).
- Weights tokens and hashtags using view velocity and like ratios:
  $$\text{Weight} = \log_{10}(\text{Views} + 1) \times \left(1.0 + \frac{\text{Likes}}{\text{Views} + 100}\right)$$
- Categorizes topics into:
  - **Previous Topics:** Content matching your existing curriculum tracks (e.g., *Claude*, *ChatGPT*, *NotebookLM*).
  - **Emerging New Topics:** High-velocity clusters covering new areas (e.g., *AI Coding & IDEs*, *AI Agents & Automation*).
- Outputs findings to `booming_trends.json`.

### Stage 2: Video Quality Curation
- Reads the booming topics from `booming_trends.json`.
- Runs targeted searches on YouTube for each topic within the lookback window.
- Ranks candidate videos using a quality score:
  $$\text{Score} = \left(0.5 \times \log_{10}(\text{Views} + 1)\right) + \left(50.0 \times \frac{\text{Likes}}{\text{Views} + 100}\right)$$
- Picks the top videos per topic (default: 6).
- Automatically detects the last `Sr No` and date in `Training.xlsx` and appends the new rows with styled formatting and clickable hyperlinks.

---

## Directory Structure

```text
ai-pulse-curator/
│
├── .env                        # Local secrets (API keys - excluded from Git)
├── .gitignore                   # Excludes caches, venvs, and sensitive credentials
├── LICENSE                      # MIT Open-Source License
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── step1_trend_analyzer.py      # Stage 1: Detects booming keywords, tags & topics
├── step2_video_curator.py       # Stage 2: Ranks videos & syncs Training.xlsx
├── booming_trends.json          # Intermediate data handoff between Stage 1 and 2
└── Training.xlsx                # Master organizational training spreadsheet
