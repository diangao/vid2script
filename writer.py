import json
import logging
from typing import List, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_timestamp(seconds: float) -> str:
    """
    Formats seconds into [HH:MM:SS] format.
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"[{int(h):02d}:{int(m):02d}:{int(s):02d}]"

class TranscriptWriter:
    """
    Handles writing the generated transcript data to a file.
    """
    def write(self, transcript_data: List[Dict[str, Any]], output_path: str):
        """
        Writes the transcript data to the specified output file.

        The format is determined by the file extension (.txt or .json).

        Args:
            transcript_data (List[Dict[str, Any]]): A list of dictionaries,
                each containing 'timestamp' and 'dialogue'.
            output_path (str): The path to the output file.
        
        Raises:
            ValueError: If the output file format is not supported.
        """
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        _, extension = os.path.splitext(output_path)

        logging.info(f"Writing transcript to {output_path} in {extension} format...")

        if extension.lower() == '.txt':
            self._write_txt(transcript_data, output_path)
        elif extension.lower() == '.json':
            self._write_json(transcript_data, output_path)
        else:
            raise ValueError(f"Unsupported output file format: {extension}. Please use '.txt' or '.json'.")
        
        logging.info("Successfully wrote transcript.")

    def _write_txt(self, transcript_data: List[Dict[str, Any]], output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in transcript_data:
                timestamp_str = format_timestamp(item['timestamp'])
                dialogue = item['dialogue']
                f.write(f"{timestamp_str}\n")
                f.write(f"{dialogue}\n\n")

    def _write_json(self, transcript_data: List[Dict[str, Any]], output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    # Example usage for testing the module directly
    writer = TranscriptWriter()
    
    # Create some dummy transcript data
    dummy_data = [
        {
            "timestamp": 2.5,
            "dialogue": "用户：这是什么？\nAI 助手：这看起来像一个电路板。"
        },
        {
            "timestamp": 7.8,
            "dialogue": "用户：那个最大的黑色方块是什么？\nAI 助手：那是主处理芯片，负责设备的核心计算。"
        },
        {
            "timestamp": 15.2,
            "dialogue": "用户：旁边这些小的是什么？\nAI 助手：这些是电容和电阻，用于稳定电流和电压。"
        }
    ]

    txt_output_path = "test_output/transcript.txt"
    json_output_path = "test_output/transcript.json"

    print(f"--- Testing TranscriptWriter ---")
    
    try:
        # Test writing to .txt
        print(f"Attempting to write to {txt_output_path}...")
        writer.write(dummy_data, txt_output_path)
        print(f"Successfully created {txt_output_path}.")
        with open(txt_output_path, 'r', encoding='utf-8') as f:
            print("\n--- Content of transcript.txt ---")
            print(f.read())

        # Test writing to .json
        print(f"Attempting to write to {json_output_path}...")
        writer.write(dummy_data, json_output_path)
        print(f"Successfully created {json_output_path}.")
        with open(json_output_path, 'r', encoding='utf-8') as f:
            print("\n--- Content of transcript.json ---")
            print(f.read())
            
        print("--- Test Complete ---")

    except (ValueError, IOError) as e:
        print(f"An error occurred during testing: {e}") 