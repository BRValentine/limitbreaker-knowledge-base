import os
import glob

# Paths
transcripts_dir = "transcripts"
output_file = "transcripts/all_transcripts.txt"

# Ensure output directory exists
os.makedirs(transcripts_dir, exist_ok=True)

# Get all .vtt files
vtt_files = glob.glob(os.path.join(transcripts_dir, "*.vtt"))

# Combine transcripts
with open(output_file, 'w', encoding='utf-8') as outfile:
    for vtt_file in vtt_files:
        video_id = os.path.basename(vtt_file).split('.')[0]
        with open(vtt_file, 'r', encoding='utf-8') as infile:
            outfile.write(f"Transcript for Video ID {video_id}:\n")
            outfile.write(infile.read())
            outfile.write("\n\n---\n\n")

print(f"Combined transcripts saved to {output_file}")