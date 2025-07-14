from typing import List, Dict, Any

class PromptBuilder:
    """
    Constructs a prompt for the Claude Vision API to generate a dialogue script
    based on video frames.
    """
    def __init__(self):
        """
        Initializes the PromptBuilder with a predefined system prompt.
        """
        self.system_prompt = """
You are a professional scriptwriter. Your task is to watch a series of consecutive video frames and generate a natural dialogue script based solely on these visual inputs.

**Character Roles:**
- **User:** Casual tone, curious. Asks questions or expresses immediate thoughts.
- **AI Assistant:** Professional tone, explanatory, proactively highlights key points, informativem, and can't make any factual mistakes.

**Rules:**
1. **Strictly Based on Visual Information:** The script must strictly revolve around the people, objects, actions, and scenes shown in the provided images. No imagined content or information not present in the images is allowed.
2. **Natural Dialogue:** Generate a short conversation containing 2-4 dialogue turns (1-2 complete back-and-forth exchanges between "User" and "AI Assistant").
3. **Specified Format:** Output must strictly follow the format below, containing only character names and lines, without any additional explanations, titles, or preamble.
   Example:
   User: What's this?
   AI Assistant: This is the internal structure of a door lock, you can see the sensor embedded in the upper right corner.

**Task:**
Please analyze the following series of images and, following all the rules above, generate a dialogue script between the "User" and "AI Assistant".
"""

    def build(self, frames: List[str]) -> List[Dict[str, Any]]:
        """
        Builds the user-facing part of the prompt with image data.

        Args:
            frames (List[str]): A list of Base64 encoded frame strings.

        Returns:
            List[Dict[str, Any]]: A list of content blocks formatted for the
                                  Claude API.
        """
        if not frames:
            raise ValueError("Frames list cannot be empty.")

        user_content = [
            {
                "type": "text",
                "text": "Please create a dialogue script based on these consecutive images."
            }
        ]

        for base64_image in frames:
            user_content.insert(0, {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image,
                },
            })

        return user_content

if __name__ == '__main__':
    # Example usage for testing the module directly
    builder = PromptBuilder()

    # Create some dummy base64 strings for testing
    # In a real scenario, these would come from the VideoChunker
    dummy_frame_1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    dummy_frame_2 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    frames_list = [dummy_frame_1, dummy_frame_2]
    
    prompt_content = builder.build(frames_list)
    system_prompt = builder.system_prompt

    print("--- System Prompt ---")
    print(system_prompt)
    
    print("\n--- User Content (for API call) ---")
    # To keep the output clean, we'll just show the structure and types
    for item in prompt_content:
        if item['type'] == 'text':
            print(f"Type: {item['type']}, Text: {item['text']}")
        elif item['type'] == 'image':
            print(f"Type: {item['type']}, Media Type: {item['source']['media_type']}, Data: {item['source']['data'][:20]}...")

    print(f"\nTotal content blocks: {len(prompt_content)}") 