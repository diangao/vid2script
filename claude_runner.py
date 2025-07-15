import anthropic
import os
import logging
import time
from typing import List, Dict, Any, Optional
from prompt_builder import PromptBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeRunner:
    """
    Handles the interaction with the Anthropic Claude API for generating dialogue scripts.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307", max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initializes the ClaudeRunner.

        Args:
            api_key (Optional[str]): API key for Anthropic API. If None, reads from environment.
            model (str): Claude model to use. Defaults to claude-3-haiku-20240307 (cheapest with vision).
                        Options: 
                        - claude-3-haiku-20240307 (cheapest, good performance)
                        - claude-3-5-sonnet-20241022 (most capable, more expensive)
                        - claude-3-opus-20240229 (highest quality, most expensive)
            max_retries (int): Maximum number of retries for failed API calls.
            retry_delay (float): Delay between retries in seconds.
        
        Raises:
            ValueError: If the API key is not provided and not found in environment.
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided either as parameter or environment variable")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.prompt_builder = PromptBuilder()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Model configuration - now defaults to Haiku for cost efficiency
        self.model = model
        self.max_tokens = 1024
        
        # Log the model being used for transparency
        model_costs = {
            "claude-3-haiku-20240307": "最便宜 💰",
            "claude-3-5-sonnet-20241022": "中等价格 💰💰", 
            "claude-3-opus-20240229": "最贵 💰💰💰"
        }
        cost_info = model_costs.get(self.model, "未知")
        logger.info(f"使用模型: {self.model} ({cost_info})")

    def generate_dialogue(self, frames: List[str], timestamp: str = "", context: Optional[str] = None, duration: Optional[float] = None) -> Optional[str]:
        """
        Generate a dialogue script from video frames using Claude Vision API.
        
        Args:
            frames (List[str]): List of base64-encoded image frames.
            timestamp (str): Timestamp for this video segment (for logging purposes).
            context (Optional[str]): Previous dialogue content to avoid repetition.
            duration (Optional[float]): Duration of the video segment in seconds.
            
        Returns:
            Optional[str]: Generated dialogue script, or None if failed.
        """
        if not frames:
            logger.warning("No frames provided for dialogue generation")
            return None
            
        try:
            # Build the prompt content with context and duration
            user_content = self.prompt_builder.build(frames, context=context, duration=duration)
            
            # Make API call with retries
            response = self._call_claude_with_retry(user_content, timestamp)
            
            if response:
                # Clean and format the response
                cleaned_dialogue = self._clean_response(response)
                logger.info(f"Successfully generated dialogue for timestamp {timestamp}")
                return cleaned_dialogue
            else:
                logger.error(f"Failed to generate dialogue for timestamp {timestamp}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating dialogue for timestamp {timestamp}: {str(e)}")
            return None
    
    def _call_claude_with_retry(self, user_content: List[Dict[str, Any]], timestamp: str) -> Optional[str]:
        """
        Call Claude API with retry logic.
        
        Args:
            user_content (List[Dict[str, Any]]): The content to send to Claude.
            timestamp (str): Timestamp for logging.
            
        Returns:
            Optional[str]: API response text or None if all retries failed.
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Calling Claude API (attempt {attempt + 1}/{self.max_retries}) for timestamp {timestamp}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.prompt_builder.system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_content
                    }]
                )
                
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    logger.warning(f"Empty response from Claude API for timestamp {timestamp}")
                    
            except anthropic.RateLimitError as e:
                logger.warning(f"Rate limit hit for timestamp {timestamp}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Waiting {sleep_time} seconds before retry...")
                    time.sleep(sleep_time)
                    
            except anthropic.APIError as e:
                logger.error(f"Claude API error for timestamp {timestamp}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"Unexpected error for timestamp {timestamp}, attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        logger.error(f"All {self.max_retries} attempts failed for timestamp {timestamp}")
        return None
    
    def _clean_response(self, response_text: str) -> str:
        """
        Clean and format the response from Claude API.
        
        Args:
            response_text (str): Raw response from Claude.
            
        Returns:
            str: Cleaned dialogue script.
        """
        if not response_text:
            return ""
        
        # Remove any markdown formatting if present
        cleaned = response_text.strip()
        
        # Remove code block markers if present
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            if len(lines) > 2:
                cleaned = '\n'.join(lines[1:-1])
        
        # Ensure consistent line endings
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        return cleaned
    
    def batch_generate(self, frames_list: List[List[str]], timestamps: List[str]) -> List[Dict[str, Any]]:
        """
        Generate dialogue scripts for multiple video segments.
        
        Args:
            frames_list (List[List[str]]): List of frame lists, each representing a video segment.
            timestamps (List[str]): List of timestamps corresponding to each segment.
            
        Returns:
            List[Dict[str, Any]]: List of results with timestamp and dialogue pairs.
        """
        if len(frames_list) != len(timestamps):
            raise ValueError("frames_list and timestamps must have the same length")
        
        results = []
        total_segments = len(frames_list)
        
        logger.info(f"Starting batch generation for {total_segments} segments")
        
        for i, (frames, timestamp) in enumerate(zip(frames_list, timestamps)):
            logger.info(f"Processing segment {i + 1}/{total_segments} at {timestamp}")
            
            dialogue = self.generate_dialogue(frames, timestamp)
            
            result = {
                "timestamp": timestamp,
                "dialogue": dialogue,
                "success": dialogue is not None
            }
            
            results.append(result)
            
            # Add a small delay between requests to be respectful to the API
            if i < total_segments - 1:  # Don't sleep after the last request
                time.sleep(0.5)
        
        successful_count = sum(1 for r in results if r["success"])
        logger.info(f"Batch generation completed: {successful_count}/{total_segments} segments successful")
        
        return results

if __name__ == '__main__':
    # This example demonstrates how to use the ClaudeRunner.
    # It requires a .env file in the project root with your ANTHROPIC_API_KEY.
    from dotenv import load_dotenv
    from prompt_builder import PromptBuilder

    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in .env file.")
        print("Please create a .env file in the root directory and add your key, e.g.:")
        print("ANTHROPIC_API_KEY='sk-ant-...'")
    else:
        try:
            # 1. Create a sample prompt using PromptBuilder
            builder = PromptBuilder()
            system_prompt = builder.system_prompt
            
            # For testing, we use dummy frames. In the real script, these come from VideoChunker.
            # To actually test vision capabilities, replace these with real base64 image strings.
            dummy_frame = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            user_content = builder.build(frames=[dummy_frame])

            # 2. Initialize and run the ClaudeRunner
            runner = ClaudeRunner(api_key=api_key)
            
            print("--- Sending a test request to Claude ---")
            print("Note: This test uses a dummy blank image and will not produce meaningful visual results.")
            print("It primarily serves to verify API connectivity and prompt structure.")
            
            # For this test, we modify the user text to be more direct since the image is blank
            user_content[-1]['text'] = "请基于你对一个现代智能门锁内部结构的了解，模拟一段“用户”和“AI助手”的对话。"

            dialogue = runner.run(system_prompt, user_content)

            # 3. Print the result
            print("\n--- Generated Dialogue ---")
            print(dialogue)
            print("\n--- Test Complete ---")

        except (ValueError, anthropic.APIError) as e:
            print(f"\nAn error occurred during the test: {e}") 