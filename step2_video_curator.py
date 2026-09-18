"""
STEP 2: Best Out of Best Video Curator (Last 2 Weeks)
-----------------------------------------------------
Scores videos by engagement/view ratio and appends
styled rows directly into Training.xlsx.
"""

import os
import json
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

class VideoCurator:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.service = None
        if self.api_key:
            try:
                from googleapiclient.discovery import build
                self.service = build("youtube", "v3", developerKey=self.api_key)
                print("Connected to YouTube Data API v3.")
            except Exception as e:
                print(f"Warning: Could not connect to YouTube API: {e}")

    def search_best_videos_for_topic(self, topic: str, lookback_days: int = 14, max_results: int = 6) -> List[Dict[str, Any]]:
        if self.service:
            return self._fetch_live_topic_videos(topic, lookback_days, max_results)
        return self._get_mock_topic_videos(topic, max_results)

    def _fetch_live_topic_videos(self, topic: str, lookback_days: int, max_results: int) -> List[Dict[str, Any]]:
        published_after = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        query = f"{topic} tutorial AI 2026"
        videos = []
        try:
            res = self.service.search().list(
                q=query, part="snippet", maxResults=20, order="viewCount",
                publishedAfter=published_after, type="video"
            ).execute()

            vids = [item["id"]["videoId"] for item in res.get("items", []) if "videoId" in item.get("id", {})]
            if not vids:
                return []

            stats_res = self.service.videos().list(id=",".join(vids), part="statistics,snippet").execute()
            for item in stats_res.get("items", []):
                vid = item["id"]
                sn = item.get("snippet", {})
                st = item.get("statistics", {})
                views = int(st.get("viewCount", 0))
                likes = int(st.get("likeCount", 0))
                score = (math.log10(views + 1) * 0.5) + ((likes / (views + 100)) * 50.0)

                videos.append({
                    "video_id": vid,
                    "title": sn.get("title", ""),
                    "author": sn.get("channelTitle", ""),
                    "published_at": sn.get("publishedAt", "")[:10],
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "view_count": views,
                    "like_count": likes,
                    "score": round(score, 2)
                })

            videos.sort(key=lambda x: x["score"], reverse=True)
            return videos[:max_results]

        except Exception as e:
            print(f"API Error fetching '{topic}': {e}. Using fallback generator.")
            return self._get_mock_topic_videos(topic, max_results)

    def _get_mock_topic_videos(self, topic: str, max_results: int) -> List[Dict[str, Any]]:
        base_date = datetime.now()
        curated_db = {
            "Claude": [
                ("WSPChlfxJyA", "Full Claude Tutorial: Beginner to Advanced in 19 Minutes", "Futurepedia", 350000, 11600),
                ("BAu4Y_kKqJ8", "Claude 3.5 Artifacts: Build Full Web Apps and Dashboards", "Kevin Stratvert", 180000, 9400),
                ("5Pcsqx-CbQY", "How Anthropic Engineers ACTUALLY Prompt Claude Code", "AI Foundations", 145000, 8900),
                ("Q1KT9ugTL1E", "Why I Switched from ChatGPT to Claude (You Should TOO)", "Ishan Sharma", 220000, 13500)
            ],
            "AI Coding & IDEs": [
                ("ocMOZpuAMw4", "Cursor Tutorial for Beginners (AI Code Editor)", "Tech With Tim", 1131000, 15400),
                ("Tv8mLrLtyxo", "Cursor 3.0 - Full Course for Beginners", "Tech With Tim", 104000, 2000),
                ("oQDCAJnr1aU", "Cursor AI Tutorial for Beginners: Build App with AI (2026)", "Mikey No Code", 164000, 1100)
            ],
            "AI Agents & Automation": [
                ("PfdnYe2690E", "n8n AI Agent Tutorial for Beginners 2026 - Step by Step", "Metics Media", 134000, 2900),
                ("JSA2oezQWOU", "Make.com Automation Tutorial for Beginners", "Kevin Stratvert", 967000, 18900),
                ("UV81LAb3x2g", "crewAI Crash Course For Beginners: Multi-Agent Systems", "Krish Naik", 153000, 2700)
            ],
            "NotebookLM": [
                ("EOmgC3-hznM", "Learn 80% of NotebookLM in Under 13 Minutes!", "Jeff Su", 1770000, 39000),
                ("uSVBfyHBiDU", "How to Use Google NotebookLM (Full Tutorial)", "Kevin Stratvert", 341000, 5700)
            ],
            "Chatgpt": [
                ("FKLr3ft8ea0", "Master Data Analysis with ChatGPT (in just 12 minutes)", "Jeff Su", 399000, 11000),
                ("0Q1AQAxpdGg", "How to Create Custom GPT | OpenAI Tutorial", "Kevin Stratvert", 494000, 9200)
            ]
        }

        matched_key = next((k for k in curated_db if k.lower() in topic.lower() or topic.lower() in k.lower()), "Claude")
        items = curated_db.get(matched_key)
        res = []
        for i, (vid, title, author, views, likes) in enumerate(items[:max_results]):
            dt = (base_date - timedelta(days=i + 1)).strftime("%Y-%m-%d")
            score = round((math.log10(views + 1) * 0.5) + ((likes / (views + 100)) * 50.0), 2)
            res.append({
                "video_id": vid,
                "title": title,
                "author": author,
                "published_at": dt,
                "video_url": f"https://www.youtube.com/watch?v={vid}",
                "view_count": views,
                "like_count": likes,
                "score": score
            })
        return res

def save_to_excel(curated_data: Dict[str, List[Dict[str, Any]]], excel_path: str):
    navy_header = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    reg_font = Font(name="Calibri", size=11)
    link_font = Font(name="Calibri", size=11, color="0563C1", underline="single")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
    )

    last_sr_no = 0
    last_date = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                try:
                    if row and row[0]:
                        s_val = int(row[0])
                        if s_val > last_sr_no:
                            last_sr_no = s_val
                    if row and len(row) > 1 and row[1]:
                        last_date = str(row[1])[:10]
                except:
                    pass
        except Exception:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Training"
            ws.append(["Sr No", "Date", "Author", "Topic", "Title", "Video Url", "Status"])
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Training"
        ws.append(["Sr No", "Date", "Author", "Topic", "Title", "Video Url", "Status"])

    for col in range(1, 8):
        c = ws.cell(row=1, column=col)
        c.fill = navy_header
        c.font = header_font
        c.alignment = Alignment(horizontal="center")

    current_sr = last_sr_no + 1
    cur_date_obj = datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1) if last_date else datetime.now()

    added_count = 0
    for topic, vids in curated_data.items():
        for v in vids:
            date_str = cur_date_obj.strftime("%Y-%m-%d")
            row_vals = [
                current_sr,
                date_str,
                v.get("author", ""),
                topic,
                v.get("title", ""),
                v.get("video_url", ""),
                "Pending"
            ]
            ws.append(row_vals)
            row_idx = ws.max_row

            for col_idx, val in enumerate(row_vals, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = reg_font
                cell.border = thin_border
                if col_idx in (1, 2):
                    cell.alignment = Alignment(horizontal="center")
                elif col_idx == 6 and val:
                    cell.font = link_font
                    cell.hyperlink = val

            current_sr += 1
            cur_date_obj += timedelta(days=1)
            added_count += 1

    for col in ws.columns:
        m = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[openpyxl.utils.get_column_letter(col[0].column)].width = min(max(m + 3, 12), 55)

    wb.save(excel_path)
    print(f"\n✅ Appended {added_count} new curated videos to '{excel_path}' (Sr No {last_sr_no + 1} to {current_sr - 1}).")

def main():
    print("=" * 75)
    print("🎬 STEP 2: BEST OUT OF BEST YOUTUBE AI VIDEO CURATOR (LAST 2 WEEKS)")
    print("=" * 75)

    default_key = os.getenv("YOUTUBE_API_KEY", "")
    api_key = input("Enter YouTube API Key [Press Enter to use ENV / demo mode]: ").strip() or default_key

    print("\nHow would you like to provide the booming topics from Step 1?")
    print("  [1] Auto-load from 'booming_trends.json' (Recommended)")
    print("  [2] Manually paste or type topics / keywords")
    choice = input("Enter choice (1 or 2) [Default: 1]: ").strip() or "1"

    target_topics = []
    if choice == "1" and os.path.exists("booming_trends.json"):
        with open("booming_trends.json") as f:
            data = json.load(f)
            target_topics = [t["topic"] for t in data.get("booming_topics", [])][:6]
        print(f"📖 Loaded {len(target_topics)} booming topics from 'booming_trends.json':")
        for i, t in enumerate(target_topics, 1):
            print(f"   {i}. {t}")
    else:
        manual_input = input("\nEnter topics separated by commas (e.g., Claude, AI Agents, Cursor AI): ").strip()
        target_topics = [t.strip() for t in manual_input.split(",") if t.strip()]

    if not target_topics:
        target_topics = ["Claude", "AI Coding & IDEs", "NotebookLM", "AI Agents & Automation", "Chatgpt"]

    raw_path = input("\nEnter path to Excel sheet to update [Default: Training.xlsx]: ").strip()
    excel_path = raw_path or "Training.xlsx"

    num_str = input("How many videos per topic? [Default: 6]: ").strip()
    videos_per_topic = int(num_str) if num_str.isdigit() else 6

    curator = VideoCurator(api_key=api_key)
    curated_results = {}

    print("\n" + "=" * 75)
    print("🔍 CURATING BEST OUT OF BEST VIDEOS (LAST 2 WEEKS)")
    print("=" * 75)

    for topic in target_topics:
        print(f"\n🔎 Finding top {videos_per_topic} videos for topic: '{topic}'...")
        vids = curator.search_best_videos_for_topic(topic, lookback_days=14, max_results=videos_per_topic)
        curated_results[topic] = vids
        for idx, v in enumerate(vids, 1):
            print(f"   [{idx}] {v['title']}")
            print(f"       Channel: {v['author']} | Views: {v['view_count']:,} | Likes: {v['like_count']:,} | Score: {v['score']}")
            print(f"       URL: {v['video_url']}")

    save_to_excel(curated_results, excel_path)

    print("\n" + "=" * 75)
    print("🎉 CURATION COMPLETE! All best videos have been appended to your Excel file.")
    print("=" * 75)

if __name__ == "__main__":
    main()
