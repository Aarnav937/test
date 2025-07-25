from groq import Groq
from dotenv import dotenv_values
import os

# Load environment variables
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username", "User")

# Initialize Groq client only if API key exists
client = None
if GroqAPIKey:
    client = Groq(api_key=GroqAPIKey)

# The system prompt sets the personality and instructions for the chatbot.
SystemPrompt = f"You are a helpful assistant. The user's name is {Username}."


def ChatBot(Query, chat_history: list):
    """
    This function takes a user's query and the conversation history,
    then returns the AI's response.
    """
    if not client:
        print("Error: Groq API key not found. Please check your .env file.")
        return "Chatbot is offline. The Groq API key is missing."

    try:
        # Combine the system prompt with the existing chat history and the new query
        messages_payload = [
            {"role": "system", "content": SystemPrompt}
        ] + chat_history + [
            {"role": "user", "content": Query}
        ]

        # Make the API call with the full conversation context
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # Using Llama 3 8B model for speed and quality
            messages=messages_payload,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,  # Set to False for a single, complete response
            stop=None,
        )

        response = completion.choices[0].message.content
        return response

    except Exception as e:
        print(f"Error communicating with Groq API: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now."

if __name__ == "__main__":
    # This is an example of how the function works with a history
    # The Main.py file will handle the actual history log
    history = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."}
    ]
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        # In a real run, this history would be loaded from a file
        response = ChatBot(user_input, history)
        print(f"Assistant: {response}")
        
        # Update history for the next turn in this test loop
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})