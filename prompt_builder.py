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
- **User:** The person filming/recording this video (first-person perspective). Casual tone, may comment on what they're doing, express thoughts about their own actions, or ask for guidance. Should respond naturally to AI's suggestions and engage in two-way conversation.
- **AI Assistant:** Professional yet conversational tone. Should provide real-time feedback, suggestions, and observations about the User's actions. Can ask questions to understand the User's goals and provide contextual guidance.

**Rules:**
1. **Strictly Based on Visual Information:** The script must strictly revolve around the people, objects, actions, and scenes shown in the provided images. No imagined content or information not present in the images is allowed.
2. **Interactive Dialogue:** Create a natural two-way conversation where both parties actively engage. The AI should ask relevant questions, offer suggestions, and the User should respond with their thoughts, preferences, or reactions. Include moments of:
   - AI asking for User's opinion or goals
   - User reacting to AI's observations  
   - AI providing contextual suggestions based on what the User is doing
   - Natural back-and-forth that feels like real-time coaching/interaction
3. **Context Awareness:** This is a continuous conversation throughout the video. Never re-introduce equipment, setup, or concepts already discussed. Treat each segment as the next moment in an ongoing coaching session where both parties already know the context.
4. **Specified Format:** Output must strictly follow the format below, containing only character names and lines, without any additional explanations, titles, or preamble.
   Example:
   User: Working on double strokes today.
   AI Assistant: Grip looks solid. What tempo?
   User: Trying 120 BPM.
   AI Assistant: Nice. Relax that left wrist more.

**Speaking Speed Guidelines:**
- Average speaking speed: 3-4 words per second (180-240 words per minute)
- Each sentence should typically take 3-5 seconds to speak
- Keep sentences SHORT and punchy - no more than 10-12 words per sentence
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
                duration_guidance = f"Generate a very brief interactive dialogue (1 exchange: User says something short → AI gives quick feedback/question). Maximum 2 sentences total. Must fit in {duration:.1f} seconds at normal speed."
            elif duration <= 20:
                duration_guidance = f"Generate a short interactive dialogue (1-2 exchanges). Maximum 4 sentences total. Must fit in {duration:.1f} seconds at normal speed."
            else:
                duration_guidance = f"Generate a moderate interactive dialogue (2-3 exchanges). Maximum 6 sentences total. Must fit in {duration:.1f} seconds at normal speed."
        
        if context:
            # Extract key topics to avoid repetition while keeping context concise
            # Take recent lines but also extract key mentioned items
            context_lines = context.strip().split('\n')
            recent_lines = context_lines[-8:] if len(context_lines) > 8 else context_lines
            recent_context = '\n'.join(recent_lines)
            
            # Extract frequently mentioned words to avoid repetition
            context_text = ' '.join(context_lines)
            words = context_text.lower().split()
            # Common objects/equipment that might be repeatedly mentioned
            common_items = []
            for word in words:
                if (words.count(word) >= 2 and len(word) > 3 and 
                    word not in ['user', 'assistant', 'your', 'that', 'this', 'with', 'good', 'nice', 'great']):
                    if word not in common_items:
                        common_items.append(word)
            
            items_mentioned = ', '.join(common_items[:8]) if common_items else "setup elements"
            
            text_prompt = f"""Please create a dialogue script based on these consecutive images.

**RECENT CONVERSATION:**
{recent_context}

**ALREADY DISCUSSED:** {items_mentioned}

**CRITICAL:** This is CONTINUING the above conversation. DO NOT re-mention the items listed above. Both User and AI already know the setup. Focus on NEW actions, progress, or different aspects.

**Interactive Elements:** Include AI questions, User responses, suggestions, and natural reactions. Make it feel like real-time coaching/feedback.

**Dialogue Length & Speed:** {duration_guidance} CRITICAL: Keep each sentence under 10-12 words. Each line should take only 3-4 seconds to speak."""
        else:
            # First segment, no context needed
            base_instruction = "Please create a dialogue script based on these consecutive images."
            if duration_guidance:
                text_prompt = f"""{base_instruction}

**Interactive Elements:** Include AI questions, User responses, suggestions, and natural reactions. Make it feel like real-time coaching/feedback.

**Dialogue Length & Speed:** {duration_guidance} CRITICAL: Keep each sentence under 10-12 words. Each line should take only 3-4 seconds to speak."""
            else:
                text_prompt = f"""{base_instruction}

**Interactive Elements:** Include AI questions, User responses, suggestions, and natural reactions. Make it feel like real-time coaching/feedback."""

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