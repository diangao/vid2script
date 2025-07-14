# vid2script

`vid2script` is a command-line tool that automatically generates a dialogue transcript from a video file. It leverages the visual understanding capabilities of Anthropic's Claude 3.5 Sonnet to create a natural, context-aware conversation script between a "User" and an "AI Assistant" based on the video's content.

## How it Works

The tool processes videos through a multi-step pipeline:

1.  **Video Chunking**: The video is split into smaller segments based on detected scene changes.
2.  **Frame Extraction**: A configurable number of frames are extracted from each segment to represent its visual content.
3.  **Prompt Generation**: The extracted frames are combined with conversational context from previous segments to create a multimodal prompt.
4.  **AI Dialogue Generation**: The prompt is sent to the Claude API, which generates a script for the segment.
5.  **Transcript Assembly**: The dialogue from all segments is combined, timestamped, and written to a final transcript file.

## Key Features

-   **Context-Aware Dialogue**: Maintains conversational context between chunks for a coherent and natural-sounding script.
-   **Simulated Real-Time Coaching**: The dialogue is structured as an interaction between a `User` (the person in the video) and an `AI Assistant` (a virtual coach), making it ideal for tutorials or instructional content.
-   **Timestamped Output**: Each line of dialogue is marked with a `[HH:MM:SS]` timestamp corresponding to its appearance in the video.
-   **Flexible Output Formats**: Save the transcript as a human-readable `.txt` file or a machine-readable `.json` file for further processing.
-   **Customizable Processing**: Adjust parameters like chunk duration and frames per chunk to fine-tune the output.

## Getting Started

### Prerequisites

-   Python 3.7+
-   An API key from Anthropic.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd vid2script
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your API key:**
    Create a `.env` file in the project's root directory and add your key:
    ```
    ANTHROPIC_API_KEY="your-anthropic-api-key"
    ```

## Usage

Run the script from your terminal:
```bash
python generate_transcript.py --input path/to/video.mp4 --output path/to/transcript.txt
```

### Command-Line Arguments

-   `--input` (**required**): Path to the input video file.
-   `--output` (**required**): Path for the output transcript file (`.txt` or `.json`).
-   `--min-duration` (optional): Minimum duration of a video chunk in seconds (Default: 10).
-   `--max-duration` (optional): Maximum duration of a video chunk in seconds (Default: 25).
-   `--frames-per-chunk` (optional): Number of frames to extract per chunk (Default: 3).
