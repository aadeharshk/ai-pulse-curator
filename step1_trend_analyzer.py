"""
STEP 1: Booming Trend & Topic Analyzer (Last 2 Weeks)
----------------------------------------------------
Scans recent YouTube uploads, extracts tokens/hashtags,
calculates momentum weighting, and exports booming_trends.json.
"""

import os
import re
import json
import math
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from typing import List, Dict, Any
import pandas as pd

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "him", "his", "how", "i",
    "if", "in", "into", "is", "it", "its", "just", "me", "more", "most", "my", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "our", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "with", "you", "your", "yours", "video", "tutorial", "full", "course", "guide", "learn", "watch",
    "step", "minutes", "min", "complete", "beginner", "beginners", "pro", "master", "2024", "2025", "2026",
    "best", "top", "new", "get", "use", "using", "make", "free", "like", "actually", "need", "know",
    "detailed", "covering", "features", "practical", "workflows", "real", "examples", "build", "way"
}

def extract_tokens(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    words = re.findall(r'\b[a-z0-9+#.-]{2,}\b', text)
    filtered = [w for w in words if w not in STOPWORDS and not w.isdigit()]
    phrases = []
    for idx in range(len(filtered) - 1):
        phrases.append(f"{filtered[idx]} {filtered[idx + 1]}")
    return filtered + phrases

def extract_hashtags(text: str) -> List[str]:
    return [tag.lower() for tag in re.findall(r'#(\w+)', text)]

def fetch_youtube_videos(api_key: str, lookback_days: int) -> List[Dict[str, Any]]:
    if not api_key:
        print("\n⚠️ No API key provided. Running in demo mode with sample AI videos...")
        return get_mock_recent_videos(lookback_days)

    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        published_after = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        search_terms = [
            "AI tutorial 2026", "ChatGPT", "Claude AI", "NotebookLM", 
            "Google Gemini", "AI agents", "n8n AI", "Cursor AI", 
            "Microsoft Copilot", "Prompt engineering", "AI tools"
        ]
        
        videos_by_id = {}
        print(f"\n📡 Querying YouTube Data API for the last {lookback_days} days...")
        
        for term in search_terms:
            try:
                res = youtube.search().list(
                    q=term, part="snippet", maxResults=25, order="viewCount",
                    publishedAfter=published_after, type="video"
                ).execute()
                for item in res.get("items", []):
                    vid = item.get("id", {}).get("videoId")
                    if vid and vid not in videos_by_id:
                        snippet = item.get("snippet", {})
                        videos_by_id[vid] = {
                            "video_id": vid,
                            "title": snippet.get("title", ""),
                            "description": snippet.get("description", ""),
                            "author": snippet.get("channelTitle", ""),
                            "published_at": snippet.get("publishedAt", "")[:10],
                            "video_url": f"https://www.youtube.com/watch?v={vid}",
                            "tags": []
                        }
            except Exception as e:
                print(f"Error querying '{term}': {e}")

        vids = list(videos_by_id.keys())
        for i in range(0, len(vids), 50):
            batch = vids[i:i + 50]
            stats_res = youtube.videos().list(id=",".join(batch), part="statistics,snippet").execute()
            for item in stats_res.get("items", []):
                vid = item.get("id")
                if vid in videos_by_id:
                    st = item.get("statistics", {})
                    sn = item.get("snippet", {})
                    videos_by_id[vid]["view_count"] = int(st.get("viewCount", 0))
                    videos_by_id[vid]["like_count"] = int(st.get("likeCount", 0))
                    videos_by_id[vid]["tags"] = [t.lower() for t in sn.get("tags", [])]

        return list(videos_by_id.values())

    except Exception as e:
        print(f"❌ YouTube API Error: {e}. Falling back to simulation mode.")
        return get_mock_recent_videos(lookback_days)

def get_mock_recent_videos(lookback_days: int) -> List[Dict[str, Any]]:
    base_date = datetime.now()
    raw = [
        {"title": "ChatGPT Advanced Data Analysis 2026: Master Spreadsheets & Python", "author": "Jeff Su", "views": 420000, "likes": 14000, "tags": ["chatgpt", "data analysis", "python", "excel"], "vid": "FKLr3ft8ea0"},
        {"title": "Claude 3.5 Artifacts: Build Full Web Apps & Interactive Dashboards", "author": "Kevin Stratvert", "views": 380000, "likes": 12500, "tags": ["claude", "artifacts", "nocode", "anthropic"], "vid": "BAu4Y_kKqJ8"},
        {"title": "How to Build Autonomous AI Agents with n8n & LangChain", "author": "Metics Media", "views": 290000, "likes": 11000, "tags": ["ai agents", "n8n", "langchain", "automation"], "vid": "PfdnYe2690E"},
        {"title": "Cursor AI Tutorial for Beginners: Build Full Apps 10x Faster", "author": "Tech With Tim", "views": 510000, "likes": 18000, "tags": ["cursor", "ai coding", "developer", "ide"], "vid": "ocMOZpuAMw4"},
        {"title": "Learn 80% of NotebookLM in Under 13 Minutes! (Audio Overview Podcast)", "author": "Jeff Su", "views": 1850000, "likes": 42000, "tags": ["notebooklm", "gemini", "audio overview", "podcast"], "vid": "EOmgC3-hznM"},
        {"title": "Copilot in Excel Tutorial: 7 Formulas You Will Never Need to Write Again", "author": "Kevin Stratvert", "views": 360000, "likes": 9800, "tags": ["copilot", "excel", "microsoft 365", "office"], "vid": "KXqR6VuPBlk"},
        {"title": "CrewAI Full Course: Multi-Agent Systems Explained Simply", "author": "Krish Naik", "views": 210000, "likes": 8400, "tags": ["crewai", "ai agents", "python", "multi-agent"], "vid": "UV81LAb3x2g"},
        {"title": "Make.com + AI Automation: Run Business Operations on Autopilot", "author": "Kevin Stratvert", "views": 980000, "likes": 21000, "tags": ["make.com", "ai automation", "workflow", "zapier"], "vid": "JSA2oezQWOU"}
    ]
    res = []
    for idx, item in enumerate(raw):
        dt = (base_date - timedelta(days=(idx % lookback_days) + 1)).strftime("%Y-%m-%d")
        primary_tag = item["tags"][0].replace(" ", "") if item["tags"] else "ai"
        res.append({
            "video_id": item["vid"],
            "title": item["title"],
            "description": f"Master {item['title']}. Deep dive into AI workflows. #ai #{primary_tag}",
            "author": item["author"],
            "published_at": dt,
            "video_url": f"https://www.youtube.com/watch?v={item['vid']}",
            "view_count": item["views"],
            "like_count": item["likes"],
            "tags": item["tags"]
        })
    return res

def analyze_booming_trends(videos: List[Dict[str, Any]], existing_topics: List[str]) -> Dict[str, Any]:
    keyword_counter = Counter()
    hashtag_counter = Counter()
    topic_scores = defaultdict(lambda: {"score": 0.0, "count": 0, "views": 0, "type": "Previous"})

    for v in videos:
        views = v.get("view_count", 0)
        likes = v.get("like_count", 0)
        weight = math.log10(views + 1) * (1.0 + (likes / (views + 100)))

        for token in extract_tokens(v["title"]):
            keyword_counter[token] += weight * 5.0
        for token in extract_tokens(v.get("description", "")):
            keyword_counter[token] += weight * 1.0

        tags = v.get("tags", []) + extract_hashtags(v.get("description", "") + " " + v.get("title", ""))
        for tag in tags:
            hashtag_counter[tag.lower().replace("#", "")] += weight

        title_lower = v["title"].lower()
        matched_prev = None
        for prev in existing_topics:
            if prev.lower() in title_lower:
                matched_prev = prev
                break

        if matched_prev:
            topic_scores[matched_prev]["score"] += weight
            topic_scores[matched_prev]["count"] += 1
            topic_scores[matched_prev]["views"] += views
            topic_scores[matched_prev]["type"] = "Previous Topic"
        else:
            if any(k in title_lower for k in ["agent", "n8n", "crewai", "langchain", "autogen"]):
                emerging_label = "AI Agents & Automation"
            elif any(k in title_lower for k in ["cursor", "coding", "code", "ide"]):
                emerging_label = "AI Coding & IDEs"
            elif any(k in title_lower for k in ["runway", "video", "gen-3", "kling"]):
                emerging_label = "AI Video Generation"
            elif any(k in title_lower for k in ["canvas", "artifacts"]):
                emerging_label = "AI Canvas & Artifacts"
            else:
                emerging_label = "Emerging AI Tools"

            topic_scores[emerging_label]["score"] += weight
            topic_scores[emerging_label]["count"] += 1
            topic_scores[emerging_label]["views"] += views
            topic_scores[emerging_label]["type"] = "Emerging New Topic"

    top_keywords = [k for k, count in keyword_counter.most_common(20) if len(k) > 2][:10]
    top_hashtags = [f"#{tag}" for tag, count in hashtag_counter.most_common(12) if len(tag) > 2][:8]

    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    top_topics = []
    for name, data in sorted_topics[:8]:
        top_topics.append({
            "topic": name,
            "type": data["type"],
            "video_count": data["count"],
            "total_views": data["views"],
            "momentum_score": round(data["score"], 1)
        })

    return {
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "window_days": 14,
        "booming_keywords": top_keywords,
        "booming_hashtags": top_hashtags,
        "booming_topics": top_topics
    }

def main():
    print("=" * 75)
    print("📈 STEP 1: YOUTUBE AI BOOMING TRENDS & TOPIC ANALYZER (LAST 2 WEEKS)")
    print("=" * 75)

    default_key = os.getenv("YOUTUBE_API_KEY", "")
    api_key = input("Enter YouTube API Key [Press Enter to use ENV / demo mode]: ").strip() or default_key
    raw_path = input("Enter path to existing Excel sheet [Default: Training.xlsx]: ").strip()
    excel_path = raw_path or "Training.xlsx"

    days_str = input("Enter lookback period in days [Default: 14]: ").strip()
    lookback_days = int(days_str) if days_str.isdigit() else 14

    existing_topics = []
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path) if excel_path.endswith(".xlsx") else pd.read_csv(excel_path)
            existing_topics = list(df["Topic"].dropna().unique())
            print(f"📖 Loaded {len(existing_topics)} historical topics from '{excel_path}'.")
        except Exception as e:
            print(f"Notice: Reading '{excel_path}': {e}")
    else:
        print(f"Notice: '{excel_path}' not found. Using default topic baseline.")
        existing_topics = ["ChatGPT Basics", "Claude Basics", "Gemini", "NotebookLM", "Microsoft Copilot"]

    videos = fetch_youtube_videos(api_key, lookback_days)
    print(f"✅ Ingested {len(videos)} videos from YouTube for the last {lookback_days} days.")

    trends = analyze_booming_trends(videos, existing_topics)

    print("\n" + "=" * 75)
    print(f"🔥 BOOMING RESULTS (LAST {lookback_days} DAYS / 2 WEEKS)")
    print("=" * 75)

    print("\n📌 1. BOOMING KEYWORDS:")
    for i, kw in enumerate(trends["booming_keywords"], start=1):
        print(f"   {i:2d}. {kw}")

    print("\n🏷️ 2. BOOMING HASHTAGS & TAGS:")
    print("   " + ", ".join(trends["booming_hashtags"]))

    print("\n🎯 3. BOOMING TOPICS (PREVIOUS & NEW):")
    for i, t in enumerate(trends["booming_topics"], start=1):
        badge = "🔄 [Previous Topic]" if t["type"] == "Previous Topic" else "✨ [NEW Emerging Topic]"
        print(f"   {i}. {t['topic']:<28} {badge:<22} | Videos: {t['video_count']} | Views: {t['total_views']:,}")

    output_json = "booming_trends.json"
    with open(output_json, "w") as f:
        json.dump(trends, f, indent=2)

    print("\n" + "=" * 75)
    print(f"💾 Trends automatically saved to '{output_json}'.")
    print("👉 Now run STEP 2 (`python step2_video_curator.py`) to curate the best videos!")
    print("=" * 75)

if __name__ == "__main__":
    main()
