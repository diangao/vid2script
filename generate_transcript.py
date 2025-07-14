import argparse
import os
import logging
from dotenv import load_dotenv
from tqdm import tqdm

from video_chunker import VideoChunker
from prompt_builder import PromptBuilder
from claude_runner import ClaudeRunner
from writer import TranscriptWriter

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to run the video to transcript generation process.
    """
    # 1. Setup argument parser
    parser = argparse.ArgumentParser(
        description="Generate a dialogue transcript from a video file using Claude Vision API."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to the input video file (e.g., sample.mp4)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=True, 
        help="Path to the output transcript file (e.g., transcript.txt or transcript.json)"
    )
    parser.add_argument(
        "--min-duration", 
        type=int, 
        default=10, 
        help="Minimum duration of each video chunk in seconds."
    )
    parser.add_argument(
        "--max-duration", 
        type=int, 
        default=25, 
        help="Maximum duration of each video chunk in seconds."
    )
    parser.add_argument(
        "--frames-per-chunk", 
        type=int, 
        default=3, 
        help="Number of frames to extract per chunk."
    )
    args = parser.parse_args()

    # 2. Load API Key
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logging.error("ANTHROPIC_API_KEY not found in .env file. Please create one.")
        return

    try:
        # 3. Instantiate all modules
        logging.info("Initializing modules...")
        chunker = VideoChunker(
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            frames_per_chunk=args.frames_per_chunk
        )
        builder = PromptBuilder()
        runner = ClaudeRunner(api_key=api_key)
        writer = TranscriptWriter()

        # 4. Process video
        logging.info("Starting video processing...")
        video_chunks = chunker.chunk_video(args.input)
        
        if not video_chunks:
            logging.warning("No chunks were extracted from the video. Exiting.")
            return

        full_transcript = []
        previous_dialogue = None  # Track context from previous segments
        
        # Using tqdm for a progress bar
        for chunk in tqdm(video_chunks, desc="Generating dialogue for chunks"):
            timestamp = chunk.start_time
            frames = chunk.frames
            
            tqdm.write(f"Processing chunk at {timestamp:.2f}s...")

            # Get dialogue from Claude with context awareness and duration
            dialogue = runner.generate_dialogue(frames, f"{timestamp:.2f}s", context=previous_dialogue, duration=chunk.duration)

            if dialogue:
                full_transcript.append({
                    "timestamp": timestamp,
                    "dialogue": dialogue
                })
                # Update context for next iteration
                previous_dialogue = dialogue
            else:
                tqdm.write(f"Skipping chunk at {timestamp:.2f}s due to empty dialogue response.")

        # 5. Write the final transcript
        if full_transcript:
            logging.info("All chunks processed. Writing final transcript...")
            writer.write(full_transcript, args.output)
            logging.info(f"Successfully generated transcript at {args.output}")
        else:
            logging.warning("No dialogue was generated for any chunk. Output file will not be created.")

    except Exception as e:
        logging.error(f"An error occurred during the process: {e}")
        # Reraise to show traceback for debugging
        # raise

if __name__ == "__main__":
    main() 