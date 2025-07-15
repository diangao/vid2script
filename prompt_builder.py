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
You are creating a casual, friendly conversation between two people watching the same video together in real-time. This should feel like natural internet friends chatting while watching something together.

**Character Roles:**
- **User:** The person filming/recording this video (first-person perspective). Casual, conversational tone. Often asks obvious questions, makes simple observations, or comments on what they're doing. Can be a bit naive or miss details that are obvious to others.
- **AI:** A knowledgeable friend who can also see everything in the video. Very observant, informative, and helpful. Notices details the User might miss, reads text in images, identifies objects/brands/locations. Sometimes gets excited and interrupts to point things out. Never makes factual errors about what's visible.

**CONVERSATION STYLE:**
- Casual, friendly internet chat vibe - like two friends on voice chat
- Natural interruptions and overlapping thoughts (use "-- Oh wait" "-- Actually" "-- Hold on")
- Conversational fillers and reactions ("Oh cool", "Wait what", "Haha yeah"), but don't overdo it
- User asks obvious/simple questions, AI provides informative but friendly answers
- Both can get excited, surprised, or confused naturally
- No gender assumptions - keep language neutral

**AI CAPABILITIES & REQUIREMENTS:**
- Must read and mention any visible text (signs, labels, brands, foreign text on packages, etc.)
- Identify specific objects, colors, brands, locations when visible
- Provide context and background info naturally woven into chat
- Never make factual errors about what's actually shown
- Be more informative than the User, but in a casual "oh btw" way

**CONTENT DISTRIBUTION:**
1. **30% Visual Observations**: AI should constantly point out details - "I see...", "Oh that's...", "Notice how..."
2. **70% Natural Chat**: Questions, reactions, explanations, casual banter

**NATURAL INTERRUPTION PATTERNS:**
Include 2-3 interruptions per longer conversation:
- AI interrupting: "Wait -- is that a [specific brand]?"
- User interrupting: "Oh -- what's that thing there?"
- Mid-sentence clarifications: "This looks like -- oh wait, it's actually..."

**Rules:**
1. **Strictly Based on Visual Information:** The script must strictly revolve around the people, objects, actions, and scenes shown in the provided images. No imagined content or information not present in the images is allowed.
2. **Interactive Dialogue:** Create a natural two-way conversation where both parties actively engage. The AI should ask relevant questions, offer suggestions, and the User should respond with their thoughts, preferences, or reactions.
   - AI asking for User's opinion or goals
   - User reacting to AI's observations  
   - AI providing contextual suggestions based on what the User is doing
   - Natural back-and-forth that feels like real-time coaching/interaction.
3. **Context Awareness:** This is a continuous conversation throughout the video. Never re-introduce equipment, setup, or concepts already discussed. Treat each segment as the next moment in an ongoing coaching session where both parties already know the context.
4. **Specified Format:** Output must strictly follow the format below, containing only character names and lines, without any additional explanations, titles, or preamble.
   Example:
   User: Working on double strokes today.
   AI Assistant: Grip looks solid. What tempo?
   User: Trying 120 BPM.
   AI Assistant: Nice. Relax that left wrist more.
1. **Only describe what's actually visible** - no speculation or imagination
2. **Read any text you can see** - signs, labels, packaging, etc. and naturally mention it
3. **Continuous conversation** - this is ongoing, don't re-introduce things already discussed
4. **First-person perspective** - User is experiencing this live, AI is watching with them
5. **Keep it real** - like actual friends casually chatting, not formal instruction

**STRICT TIMING CONSTRAINTS:**
- Maximum 2-3 words per second (140-180 words per minute) - A BIT SLOWER than normal speech, conversational pace
- Total dialogue must fit comfortably within provided time duration  
- Use short, casual phrases - "Yeah that's..." "Oh cool..." "Wait what..."
- If unsure, make it shorter and more casual

**OUTPUT FORMAT:**
User: [casual comment/question]
AI: [informative but friendly response]

Example style:
User: What's this thing I'm holding?
AI: Oh that's a -- wait, looks like a Roland practice pad actually.
User: Haha yeah, wasn't sure.
AI: See that logo on the bottom? Classic drum practice gear.

**Task:**
Generate a natural, casual conversation based on the video frames. Remember: User is filming/experiencing this first-person, AI can see everything too and should point out details the User might miss.
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
            
            text_prompt = f"""Continue this casual conversation based on these new video frames.

**RECENT CHAT:**
{recent_context}

**YOU'VE ALREADY TALKED ABOUT:** {items_mentioned}

**IMPORTANT:** Keep the conversation flowing naturally! Don't repeat stuff you've already covered. Focus on what's happening NOW or new things you notice.

**WHAT AI SHOULD DO:** Point out details, read any text you see, mention brands/objects. Be observant but casual about it.

**CONVERSATION VIBE:** Natural interruptions, casual reactions, User might ask obvious questions, AI gives friendly informative answers.

**{duration_guidance}** Keep sentences short and conversational - like texting friends."""
        else:
            # First segment, no context needed
            base_instruction = "Start a casual conversation based on these video frames."
            if duration_guidance:
                text_prompt = f"""{base_instruction}

**WHAT'S HAPPENING:** User is filming this first-person, AI can see everything too. This is the start of their chat.

**AI'S JOB:** Be observant! Point out details, read any text you can see, identify objects/brands naturally. Don't make factual errors.

**CONVERSATION STYLE:** Casual and friendly - like internet friends watching together. User might ask simple/obvious questions, AI gives helpful but casual answers.

**{duration_guidance}** Short, natural sentences. Include some interruptions or casual reactions."""
            else:
                text_prompt = f"""{base_instruction}

**WHAT'S HAPPENING:** User is filming this first-person, AI can see everything too. This is the start of their chat.

**AI'S JOB:** Be observant! Point out details, read any text you can see, identify objects/brands naturally. Don't make factual errors.

**CONVERSATION STYLE:** Casual and friendly - like internet friends watching together. User might ask simple/obvious questions, AI gives helpful but casual answers."""

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