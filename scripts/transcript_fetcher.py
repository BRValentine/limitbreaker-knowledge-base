import os
from youtube_transcript_api import YouTubeTranscriptApi
from git import Repo
import re
from datetime import datetime

# Configuration
REPO_PATH = r"D:\credit_repair_bot"
LINKS_FILE = os.path.join(REPO_PATH, "limitbreaker-knowledge-base", "youtube_links.txt")
TRANSCRIPTS_DIR = os.path.join(REPO_PATH, "limitbreaker-knowledge-base", "transcripts")
GITHUB_USERNAME = "BRValentine"
GITHUB_TOKEN = os.getenv("GITHUB_PAT", "YOUR_PAT_HERE")  # Fetch from environment or use placeholder
REPO_NAME = "limitbreaker-knowledge-base"

def get_video_id(url):
    """Extract YouTube video ID from URL."""
    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return video_id.group(1) if video_id else None

def fetch_transcript(video_id):
    """Fetch transcript for a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(entry["text"] for entry in transcript)
        return text
    except Exception as e:
        print(f"Error fetching transcript for video {video_id}: {e}")
        return None

def save_transcript(video_id, text):
    """Save transcript to a text file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(TRANSCRIPTS_DIR, f"{video_id}_{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename

def commit_and_push(filename):
    """Commit and push changes to GitHub."""
    try:
        repo = Repo(REPO_PATH)
        repo.git.add(filename)
        repo.index.commit(f"Add transcript for video {os.path.basename(filename)}")
        origin = repo.remote(name="origin")
        origin.push()
    except Exception as e:
        print(f"Error committing/pushing to GitHub: {e}")

def main():
    """Main function to process youtube_links.txt."""
    if not os.path.exists(LINKS_FILE):
        print(f"Error: {LINKS_FILE} not found. Please create it with YouTube URLs.")
        return

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    if not links:
        print("No valid URLs found in youtube_links.txt.")
        return

    processed_links = set()
    processed_file = os.path.join(REPO_PATH, "processed_links.txt")
    if os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as f:
            processed_links = set(line.strip() for line in f)

    for link in links:
        video_id = get_video_id(link)
        if not video_id or video_id in processed_links:
            continue

        transcript = fetch_transcript(video_id)
        if transcript:
            filename = save_transcript(video_id, transcript)
            commit_and_push(filename)
            processed_links.add(video_id)
            print(f"Processed video {video_id}")

    with open(processed_file, "w", encoding="utf-8") as f:
        f.write("\n".join(processed_links))

if __name__ == "__main__":
    main()