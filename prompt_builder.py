from typing import List, Dict, Any, Optional

class PromptBuilder:
    """
    Constructs a prompt for the Claude Vision API to generate casual, 
    friendly conversations between a User (filming first-person) and an AI 
    friend watching together, based on video frames.
    """
    def __init__(self):
        """
        Initializes the PromptBuilder with a predefined system prompt.
        """
        self.system_prompt = """
Create a casual conversation between User (filming while doing an activity) and AI (watching User work).

**CORE REQUIREMENTS:**
1. **SLOWER PACE** - 140-170 words per minute. Short, casual phrases. Fit dialogue within time duration.
2. **CONTINUOUS CHAT** - When given context, continue the existing conversation. NO repetition of discussed topics.
3. **VISUAL ACCURACY** - Only describe what's visible. Read any text you see. No speculation.

**ROLES:**
- **User:** The person filming AND doing the activity. Uses "I" language ("I'm working on...", "Let me check this..."). Casual tone, sometimes asks obvious questions about their own work.
- **AI:** Friend watching User work and answering questions or comments. Uses "you" language ("Your bike looks...", "I think that's..."). Points out response to the user's question or comment, details, reads text, gives context. Sometimes asks questions to the user.

**STYLE:** 
- Internet friends chatting while watching
- Natural interruptions with "--" 
- Reactions like "Oh cool", "Wait what"
- 40% visual observations, 60% natural chat

**ANTI-REPETITION:**
- If you discussed construction/bricks/signs already → focus on NEW details only
- User shouldn't say "Whoa, looks messy" or "You're working on..." 
- User should say "I'm working on..." / "Let me check..." (first-person)
- Build on previous observations, don't restart

**FORMAT:**
User: [first-person comment: "I'm doing...", "Let me check..."]
AI: [observant response or answers to the user's question: "Good question! ...", "Your work looks...", "You're doing..."]

Generate natural dialogue that respects the SLOWER PACE and continues previous context.
"""

    def build(self, frames: List[str], context: Optional[str] = None, duration: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Builds the user-facing part of the prompt with image data and optional context.

        Args:
            frames (List[str]): A list of Base64 encoded frame strings.
            context (Optional[str]): Previous casual conversation content to maintain flow and avoid repetition.
            duration (Optional[float]): Duration of the video segment in seconds to adjust conversation length.

        Returns:
            List[Dict[str, Any]]: A list of content blocks formatted for the
                                  Claude API to generate casual conversations.
        """
        if not frames:
            raise ValueError("Frames list cannot be empty.")

        # Build the base text prompt with duration guidance
        duration_guidance = ""
        if duration:
            # Calculate maximum words based on 2.5 words per second (conservative estimate)
            max_words = int(duration * 2.5)
            
            if duration <= 12:
                duration_guidance = f"TIMING: Keep it short! Just 1 quick exchange (User + AI). Max {max_words} words total. AI should point out something they notice. Target: {duration:.1f} seconds."
            elif duration <= 20:
                duration_guidance = f"TIMING: 2 exchanges max. Max {max_words} words total. Keep it casual and conversational. Target: {duration:.1f} seconds."
            else:
                duration_guidance = f"TIMING: Up to 3 exchanges. Max {max_words} words total. Natural chat flow with some visual observations. Target: {duration:.1f} seconds."
        
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
            
            text_prompt = f"""CONTINUE this conversation based on new video frames.

**RECENT CHAT:**
{recent_context}

**ALREADY DISCUSSED:** {items_mentioned}

**KEY:** Focus ONLY on NEW details not mentioned before. Don't repeat observations. 
**REMEMBER:** User is doing the activity, not observing someone else. User says "I'm doing..." not "You're doing..." or "Someone is doing..."

**{duration_guidance}** Build on previous chat naturally."""
        else:
            # First segment, no context needed
            if duration_guidance:
                text_prompt = f"""START a casual conversation based on these video frames.

**{duration_guidance}** User is filming while doing the activity (use "I" language). AI watches User work (use "you" language). Read any visible text."""
            else:
                text_prompt = """START a casual conversation based on these video frames.

User is filming while doing the activity (use "I" language). AI watches User work (use "you" language). Read any visible text."""

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
    context_text = "User: What's this?\nAI: Oh that's a practice pad for drums."
    prompt_content_with_context = builder.build(frames_list, context=context_text, duration=18.5)
    
    print("\n--- User Content (for API call - With Context) ---")
    for item in prompt_content_with_context:
        if item['type'] == 'text':
            print(f"Type: {item['type']}, Text: {item['text'][:150]}...")
        elif item['type'] == 'image':
            print(f"Type: {item['type']}, Media Type: {item['source']['media_type']}, Data: {item['source']['data'][:20]}...")

    print(f"\nTotal content blocks with context: {len(prompt_content_with_context)}") 