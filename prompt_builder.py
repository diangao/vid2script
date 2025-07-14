from typing import List, Dict, Any, Optional

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
- **User:** The person filming/recording this video (first-person perspective). Casual tone, may comment on what they're doing, express thoughts about their own actions, or ask for guidance.
- **AI Assistant:** Professional tone, explanatory, proactively highlights key points about what the User is doing or what's visible in their recording, informative, and can't make any factual mistakes.

**Rules:**
1. **Strictly Based on Visual Information:** The script must strictly revolve around the people, objects, actions, and scenes shown in the provided images. No imagined content or information not present in the images is allowed.
2. **Natural Dialogue:** Generate a complete conversation with realistic speaking pace. Each exchange should feel natural and connected. The User should respond to the AI Assistant's comments, creating a flowing dialogue. Each sentence should be speakable within 3-5 seconds at normal conversational speed.
3. **Context Awareness:** If context from previous dialogue is provided, avoid repeating explanations of objects or concepts already mentioned. Instead, focus on new actions, environmental details, or previously unmentioned objects.
4. **Specified Format:** Output must strictly follow the format below, containing only character names and lines, without any additional explanations, titles, or preamble.
   Example:
   User: I'm working on this drum setup today.
   AI Assistant: I can see you're practicing on a RealFeel pad - the octagonal design helps prevent rotation during your stick work.
   User: Yeah, I noticed it stays put better than my old round one.
   AI Assistant: That stability really makes a difference for consistent technique practice.

**Speaking Speed Guidelines:**
- Average speaking speed: 3-4 words per second (180-240 words per minute)
- Each sentence should typically take 3-5 seconds to speak
- Prioritize concise, natural expressions over lengthy explanations

**Task:**
Please analyze the following series of images and, following all the rules above, generate a dialogue script between the "User" (the person filming/recording) and "AI Assistant". Remember: the User is experiencing this from a first-person perspective, so their comments should reflect their own actions and viewpoint.
"""

    def build(self, frames: List[str], context: Optional[str] = None, duration: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Builds the user-facing part of the prompt with image data and optional context.

        Args:
            frames (List[str]): A list of Base64 encoded frame strings.
            context (Optional[str]): Previous dialogue content to provide context and avoid repetition.
            duration (Optional[float]): Duration of the video segment in seconds to adjust dialogue length.

        Returns:
            List[Dict[str, Any]]: A list of content blocks formatted for the
                                  Claude API.
        """
        if not frames:
            raise ValueError("Frames list cannot be empty.")

        # Build the base text prompt with duration guidance
        duration_guidance = ""
        if duration:
            if duration <= 12:
                duration_guidance = f"Generate a very brief dialogue (1-2 short exchanges, max {int(duration//4)} sentences total) that can realistically be spoken in {duration:.1f} seconds at normal speed."
            elif duration <= 20:
                duration_guidance = f"Generate a moderate dialogue (2-3 exchanges, max {int(duration//3.5)} sentences total) that can realistically be spoken in {duration:.1f} seconds at normal speed."
            else:
                duration_guidance = f"Generate a longer dialogue (3-4 exchanges, max {int(duration//3)} sentences total) that can realistically be spoken in {duration:.1f} seconds at normal speed."
        
        if context:
            # Extract key items mentioned in previous context to avoid repetition
            context_lines = context.strip().split('\n')
            recent_context = '\n'.join(context_lines[-4:]) if len(context_lines) > 4 else context
            
            text_prompt = f"""Please create a dialogue script based on these consecutive images.

**Recent conversation context (avoid repeating these topics):**
{recent_context}

**Instructions:** Continue the natural flow of conversation. Focus on NEW actions, environmental details, or previously unmentioned objects. Do NOT re-explain items already discussed in the context above. Build on the existing conversation naturally.

**Dialogue Length & Speed:** {duration_guidance} Remember: each sentence should be short enough to speak naturally in 3-5 seconds."""
        else:
            # First segment, no context needed
            base_instruction = "Please create a dialogue script based on these consecutive images."
            if duration_guidance:
                text_prompt = f"{base_instruction}\n\n**Dialogue Length & Speed:** {duration_guidance} Remember: each sentence should be short enough to speak naturally in 3-5 seconds."
            else:
                text_prompt = base_instruction

        user_content = [
            {
                "type": "text",
                "text": text_prompt
            }
        ]

        # Add image frames (insert at beginning to maintain original order)
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
    
    # Test without context (first segment)
    prompt_content = builder.build(frames_list)
    system_prompt = builder.system_prompt

    print("--- System Prompt ---")
    print(system_prompt)
    
    print("\n--- User Content (for API call - No Context) ---")
    # To keep the output clean, we'll just show the structure and types
    for item in prompt_content:
        if item['type'] == 'text':
            print(f"Type: {item['type']}, Text: {item['text'][:100]}...")
        elif item['type'] == 'image':
            print(f"Type: {item['type']}, Media Type: {item['source']['media_type']}, Data: {item['source']['data'][:20]}...")

    print(f"\nTotal content blocks: {len(prompt_content)}")
    
    # Test with context and duration (subsequent segment)
    context_text = "User: What's this?\nAI Assistant: This is a practice pad used for drum practice."
    prompt_content_with_context = builder.build(frames_list, context=context_text, duration=18.5)
    
    print("\n--- User Content (for API call - With Context) ---")
    for item in prompt_content_with_context:
        if item['type'] == 'text':
            print(f"Type: {item['type']}, Text: {item['text'][:150]}...")
        elif item['type'] == 'image':
            print(f"Type: {item['type']}, Media Type: {item['source']['media_type']}, Data: {item['source']['data'][:20]}...")

    print(f"\nTotal content blocks with context: {len(prompt_content_with_context)}") 