import argparse
import os
import logging
import glob
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

from video_chunker import VideoChunker
from prompt_builder import PromptBuilder
from claude_runner import ClaudeRunner
from writer import TranscriptWriter

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_video_files(input_path: str) -> list:
    """
    Get list of video files from input path (file or directory).
    
    Args:
        input_path (str): Path to video file or directory containing videos
        
    Returns:
        list: List of video file paths
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    video_files = []
    
    if os.path.isfile(input_path):
        # Single file provided
        if any(input_path.lower().endswith(ext) for ext in video_extensions):
            video_files.append(input_path)
        else:
            logger.error(f"File {input_path} is not a supported video format")
    elif os.path.isdir(input_path):
        # Directory provided - find all video files
        for ext in video_extensions:
            pattern = os.path.join(input_path, f"*{ext}")
            video_files.extend(glob.glob(pattern))
            # Also check uppercase extensions
            pattern = os.path.join(input_path, f"*{ext.upper()}")
            video_files.extend(glob.glob(pattern))
    else:
        logger.error(f"Input path {input_path} does not exist")
    
    return sorted(video_files)

def generate_output_filename(video_path: str, output_dir: str = None) -> str:
    """
    Generate output transcript filename based on video filename.
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Optional output directory. If None, uses video's directory
        
    Returns:
        str: Generated transcript filename
    """
    video_name = Path(video_path).stem  # Get filename without extension
    transcript_filename = f"{video_name}.txt"
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, transcript_filename)
    else:
        # Use the same directory as the video file
        video_dir = os.path.dirname(video_path)
        return os.path.join(video_dir, transcript_filename)

def process_single_video(video_path: str, output_path: str, chunker: VideoChunker, 
                        builder: PromptBuilder, runner: ClaudeRunner, writer: TranscriptWriter) -> bool:
    """
    Process a single video file and generate transcript.
    
    Args:
        video_path (str): Path to video file
        output_path (str): Path for output transcript file
        chunker, builder, runner, writer: Initialized processing modules
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Processing video: {os.path.basename(video_path)}")
        
        # Process video chunks
        video_chunks = chunker.chunk_video(video_path)
        
        if not video_chunks:
            logger.warning(f"No chunks extracted from {video_path}")
            return False

        full_transcript = []
        all_previous_dialogue = ""  # Track cumulative context
        
        # Process each chunk with progress bar
        chunk_progress = tqdm(video_chunks, desc=f"Processing {os.path.basename(video_path)}", 
                            leave=False, position=1)
        
        for chunk in chunk_progress:
            timestamp = chunk.start_time
            frames = chunk.frames
            
            chunk_progress.set_postfix({"timestamp": f"{timestamp:.1f}s"})
            
            # Get dialogue from Claude with context
            context_to_pass = all_previous_dialogue if all_previous_dialogue else None
            dialogue = runner.generate_dialogue(frames, f"{timestamp:.2f}s", 
                                               context=context_to_pass, duration=chunk.duration)

            if dialogue:
                full_transcript.append({
                    "timestamp": timestamp,
                    "dialogue": dialogue
                })
                all_previous_dialogue += dialogue + "\n"
            else:
                logger.warning(f"Skipping chunk at {timestamp:.2f}s for {video_path}")

        # Write transcript
        if full_transcript:
            writer.write(full_transcript, output_path)
            logger.info(f"Successfully generated transcript: {output_path}")
            return True
        else:
            logger.warning(f"No dialogue generated for {video_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {video_path}: {str(e)}")
        return False

def main():
    """
    Main function to run the video to transcript generation process.
    """
    # 1. Setup argument parser
    parser = argparse.ArgumentParser(
        description="Generate dialogue transcripts from video files using Claude Vision API. "
                   "Supports single files or batch processing of directories."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to video file or directory containing video files"
    )
    parser.add_argument(
        "--output-dir", 
        "--output",
        type=str, 
        help="Output directory for transcript files. If not specified, uses same directory as input videos."
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
    parser.add_argument(
        "--max-videos",
        type=int,
        help="Maximum number of videos to process (useful for testing)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-haiku-20240307",
        choices=["claude-3-haiku-20240307", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        help="Claude model to use for vision processing. Haiku is cheapest, Sonnet is balanced, Opus is most capable but expensive."
    )
    args = parser.parse_args()

    # 2. Load API Key
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in .env file. Please create one.")
        return

    # 3. Get list of video files
    video_files = get_video_files(args.input)
    
    if not video_files:
        logger.error("No video files found in the specified input path")
        return
    
    # Limit number of videos if specified
    if args.max_videos:
        video_files = video_files[:args.max_videos]
    
    logger.info(f"Found {len(video_files)} video file(s) to process")
    logger.info(f"Using Claude model: {args.model}")
    
    # Print list of videos to be processed
    for i, video_path in enumerate(video_files, 1):
        logger.info(f"  {i}. {os.path.basename(video_path)}")

    try:
        # 4. Initialize modules
        logger.info("Initializing processing modules...")
        chunker = VideoChunker(
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            frames_per_chunk=args.frames_per_chunk
        )
        builder = PromptBuilder()
        runner = ClaudeRunner(api_key=api_key, model=args.model)
        writer = TranscriptWriter()

        # 5. Process each video
        successful_count = 0
        failed_videos = []
        
        # Main progress bar for all videos
        video_progress = tqdm(video_files, desc="Processing videos", position=0)
        
        for video_path in video_progress:
            video_name = os.path.basename(video_path)
            video_progress.set_description(f"Processing: {video_name}")
            
            # Generate output filename
            output_path = generate_output_filename(video_path, args.output_dir)
            
            # Check if transcript already exists
            if os.path.exists(output_path):
                logger.info(f"Transcript already exists for {video_name}, skipping...")
                continue
            
            # Process the video
            success = process_single_video(video_path, output_path, chunker, builder, runner, writer)
            
            if success:
                successful_count += 1
                video_progress.set_postfix({"success": f"{successful_count}/{len(video_files)}"})
            else:
                failed_videos.append(video_name)

        # 6. Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"BATCH PROCESSING COMPLETE")
        logger.info(f"{'='*50}")
        logger.info(f"Total videos processed: {len(video_files)}")
        logger.info(f"Successful: {successful_count}")
        logger.info(f"Failed: {len(failed_videos)}")
        
        if failed_videos:
            logger.info(f"Failed videos: {', '.join(failed_videos)}")
        
        if args.output_dir:
            logger.info(f"Transcript files saved to: {args.output_dir}")
        else:
            logger.info("Transcript files saved in same directories as video files")

    except Exception as e:
        logger.error(f"An error occurred during batch processing: {e}")

if __name__ == "__main__":
    main()