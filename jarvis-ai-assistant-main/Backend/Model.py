import google.generativeai as genai
from dotenv import dotenv_values
import ast

# Load the Google API key from the .env file
env_vars = dotenv_values(".env")
GOOGLE_API_KEY = env_vars.get("GOOGLE_API_KEY")

# Configure the Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("Error: GOOGLE_API_KEY not found in .env file. The model will not work.")


# --- MODIFICATION ---
# The SystemPrompt is updated to include the new 'weather' skill.
SystemPrompt = """
You are an expert at understanding user commands and breaking them down into a series of tasks for a voice assistant.
Your goal is to convert a user's query into a machine-readable Python list of strings.

Analyze the user's query and determine the appropriate action from the list of available functions.

**Available Functions and their format:**
- open: For opening applications. Format: 'open (application name)'
- close: For closing applications. Format: 'close (application name)'
- play: For playing music or videos on YouTube. Format: 'play (song or video name)'
- system: For system commands like volume control. Format: 'system (mute/unmute/volume up/volume down)'
- content: For generating written content like letters or code. Format: 'content (topic to write about)'
- google search: For searching on Google. Format: 'google search (search query)'
- Youtube: For searching on YouTube. Format: 'Youtube (search query)'
- generate: For generating images. Format: 'generate (image description)'
- weather: For getting the current weather. Format: 'weather (city name)'
- realtime: For questions that need current, real-time information that is not weather-related. Format: 'realtime (question)'
- general: For general conversation or questions that don't fit other categories. Format: 'general (the user's original query)'
- exit: When the user wants to close the assistant. Format: 'exit'

**Your Response MUST be a valid Python list of strings.**

**Examples:**
- User Query: "open chrome and play a song by linkin park"
- Your Response: ['open chrome', 'play a song by linkin park']

- User Query: "what's the weather in New York and also generate an image of a cat"
- Your Response: ['weather New York', 'generate an image of a cat']

- User Query: "who are you"
- Your Response: ['general who are you']

- User Query: "exit the program"
- Your Response: ['exit']
"""

def FirstLayerDMM(Query: str):
    """
    Uses the Gemini model to determine the user's intent and returns a list of commands.
    """
    if not GOOGLE_API_KEY:
        return ["general I can't function without my API key. Please check the .env file."]

    try:
        # Initialize the Gemini model (gemini-1.5-flash is fast and efficient)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SystemPrompt
        )

        # Send the user's query to the model
        response = model.generate_content(Query)

        # The model's response is a string that looks like a list.
        # We use ast.literal_eval to safely convert it into a real Python list.
        decision_list = ast.literal_eval(response.text.strip())

        return decision_list

    except Exception as e:
        print(f"Error communicating with Gemini model: {e}")
        # Fallback for errors
        return [f"general {Query}"]

if __name__ == "__main__":
    while True:
        user_input = input(">>> ")
        if user_input.lower() in ["exit", "quit"]:
            break
        decision = FirstLayerDMM(user_input)
        print(decision)