import yt_dlp
import os

# Path to youtube_links.txt and output directory
links_file = "transcripts/youtube_links.txt"  # Updated path
output_dir = "transcripts"
os.makedirs(output_dir, exist_ok=True)

# yt-dlp options (no proxy needed locally)
ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['en'],
    'skip_download': True,
    'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
    'cookiefile': 'cookies.txt',
}

# Read YouTube links
with open(links_file, 'r') as f:
    urls = [line.strip() for line in f if line.strip()]

# Process each video
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    for url in urls:
        try:
            info = ydl.extract_info(url, download=False)
            if 'subtitles' in info and 'en' in info['subtitles']:
                print(f"Transcript saved for {url}")
            else:
                print(f"No English transcript for {url}")
        except Exception as e:
            print(f"Error processing {url}: {e}")