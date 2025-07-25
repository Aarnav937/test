from Frontend.GUI import (
    GraphicalUserInterface,
    SetAsssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DefaultMessage = f""" {Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you? """

# --- MODIFICATION ---
# Added 'weather' to the list of recognized functions
functions = ["open", "close", "play", "system", "content", "google search", "Youtube", "weather"]
subprocess_list = []


# --- This function is preserved from your code ---
def UpdateChatLog(user_query, assistant_answer):
    """Appends the latest user query and assistant response to the chat log."""
    try:
        # Read the existing log
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            chat_log = json.load(file)

        # Append new messages
        chat_log.append({"role": "user", "content": user_query})
        chat_log.append({"role": "assistant", "content": assistant_answer})

        # Write the updated log back to the file
        with open(r'Data\ChatLog.json', 'w', encoding='utf-8') as file:
            json.dump(chat_log, file, indent=4)

    except Exception as e:
        print(f"Error updating ChatLog.json: {e}")


# This function is preserved from your code
def ShowDefaultChatIfNoChats():
    try:
        with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as temp_file:
                    temp_file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                    response_file.write(DefaultMessage)
    except FileNotFoundError:
        print("ChatLog.json file not found. Creating default response.")
        os.makedirs("Data", exist_ok=True)
        # Create an empty list in the JSON file
        with open(r'Data\ChatLog.json', "w", encoding='utf-8') as file:
            json.dump([], file)
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
            response_file.write(DefaultMessage)

# This function is preserved from your code
def ReadChatLogJson():
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            chatlog_data = json.load(file)
        return chatlog_data
    except (FileNotFoundError, json.JSONDecodeError):
        print("ChatLog.json not found or is invalid. Returning empty list.")
        return []

# This function is preserved from your code
def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"{Username}: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"{Assistantname}: {entry['content']}\n"

    temp_dir_path = TempDirectoryPath('')
    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

# This function is preserved from your code
def ShowChatOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
            data = file.read()
        if len(str(data)) > 0:
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                response_file.write(data)
    except FileNotFoundError:
        print("Database.data file not found.")

# This function is preserved from your code
def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatOnGUI()


# --- MODIFICATION ---
# The MainExecution function is updated to handle text responses from the Automation module.
def MainExecution():
    try:
        ImageExecution = False
        ImageGenerationQuery = ""

        SetAsssistantStatus("Listening...")
        Query = SpeechRecognition()
        if not Query:
            SetAsssistantStatus("Available...")
            return

        ShowTextToScreen(f"{Username}: {Query}")
        SetAsssistantStatus("Thinking...")
        Decision = FirstLayerDMM(Query)

        print(f"\nDecision: {Decision}\n")

        CleanedDecision = [cmd.replace("general ", "").strip().replace("realtime ", "").strip() for cmd in Decision]

        G = any(i.startswith("general") for i in Decision)
        R = any(i.startswith("realtime") for i in Decision)
        A = any(any(cmd.startswith(func) for func in functions) for cmd in CleanedDecision)

        # Handle automation tasks first
        if A:
            SetAsssistantStatus("Working...")
            automation_responses = run(Automation(CleanedDecision))
            
            # If the automation returned a text response (like a weather report)
            if automation_responses and isinstance(automation_responses, list) and len(automation_responses) > 0:
                full_response = ". ".join(filter(None, automation_responses))
                
                ShowTextToScreen(f"{Assistantname}: {full_response}")
                UpdateChatLog(Query, full_response)
                SetAsssistantStatus("Answering...")
                TextToSpeech(full_response)

        # Handle image generation
        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True
        
        if ImageExecution:
            with open(r'Frontend\Files\ImageGeneration.data', "w") as file:
                file.write(f"{ImageGenerationQuery},True")
            try:
                p1 = subprocess.Popen(['python', r"Backend\ImageGeneration.py"])
                subprocess_list.append(p1)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        # Handle general or realtime chat queries
        if G or R:
            Merged_query = " and ".join(CleanedDecision)
            chat_history = ReadChatLogJson()

            if R:
                SetAsssistantStatus("Searching...")
                Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            else:
                SetAsssistantStatus("Thinking...")
                Answer = ChatBot(QueryModifier(Merged_query), chat_history)

            ShowTextToScreen(f"{Assistantname}: {Answer}")
            UpdateChatLog(Merged_query, Answer)
            SetAsssistantStatus("Answering...")
            TextToSpeech(Answer)

        # Handle exit command
        if 'exit' in Decision:
            os._exit(1)

    except Exception as e:
        print(f"Error in MainExecution: {e}")
    finally:
        # Always set status back to available unless an exit command was issued
        if 'exit' not in Decision:
             SetAsssistantStatus("Available...")


# This function is preserved from your code
def FirstThread():
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()
            if CurrentStatus is None:
                sleep(1)
                continue

            if str(CurrentStatus).lower() == "true":
                MainExecution()
                SetMicrophoneStatus("False")
            else:
                sleep(0.1)
        except Exception as e:
            print(f"Error in FirstThread: {e}")
            sleep(1)

# This function is preserved from your code
def SecondThread():
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in SecondThread: {e}")

# This function is preserved from your code
if __name__ == "__main__":
    InitialExecution()
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    SecondThread()                              
    # main.py

# ... (rest of your imports and code) ...

# The MainExecution function is updated to handle text responses from the Automation module.
def MainExecution():
    try:
        ImageExecution = False
        ImageGenerationQuery = ""

        SetAsssistantStatus("Listening...")
        Query = SpeechRecognition()
        if not Query:
            SetAsssistantStatus("Available...")
            return

        ShowTextToScreen(f"{Username}: {Query}")
        SetAsssistantStatus("Thinking...")
        Decision = FirstLayerDMM(Query)

        print(f"\nDecision: {Decision}\n")

        # Keep original Decision for processing specific command types
        # CleanedDecision is still useful for passing to Automation if it only needs the action part
        # For weather, "weather mumbai" is fine. For "general who are you", "who are you" is needed by ChatBot.
        # We'll adapt the parsing below.

        G = any(i.startswith("general") for i in Decision)
        R = any(i.startswith("realtime") for i in Decision)
        # Check if any command in the decision list is an 'automation' function
        # This is a more robust check based on the actual decision items
        is_automation_command = any(any(item.startswith(f) for f in functions) for item in Decision)
        
        overall_answer_parts = [] # Collect all parts of the answer

        # Process automation tasks if any are in the decision
        if is_automation_command:
            SetAsssistantStatus("Working...")
            # Pass the original decision list, Automation will parse it
            automation_results = run(Automation(Decision)) # Pass the full Decision list

            # Iterate through the results from Automation and add to overall_answer_parts
            if automation_results:
                for res in automation_results:
                    if res is not None and isinstance(res, str) and res.strip(): # Only add non-empty strings
                        overall_answer_parts.append(res.strip())

        # Handle image generation (can be independent or combined)
        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True
        
        if ImageExecution:
            # You might want to add a message about image generation here
            overall_answer_parts.append("I am generating an image for you.")
            with open(r'Frontend\Files\ImageGeneration.data', "w") as file:
                file.write(f"{ImageGenerationQuery},True")
            try:
                p1 = subprocess.Popen(['python', r"Backend\ImageGeneration.py"])
                subprocess_list.append(p1)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        # Handle general or realtime chat queries if they are present and not already handled by automation's direct response
        # It's important to only process these if they weren't the main intent already handled by automation.
        # This logic needs careful consideration for mixed commands.
        # For simplicity, if we processed an automation command that returned a response, we prioritize that.
        
        if not overall_answer_parts and (G or R): # Only process if no automation response yet
            Merged_query_parts = []
            for item in Decision:
                if item.startswith("general"):
                    Merged_query_parts.append(item.replace("general", "").strip())
                elif item.startswith("realtime"):
                    Merged_query_parts.append(item.replace("realtime", "").strip())
            
            Merged_query = " and ".join(filter(None, Merged_query_parts)) # Filter out empty strings
            
            if Merged_query: # Only proceed if there's a valid query after stripping
                chat_history = ReadChatLogJson()

                if R:
                    SetAsssistantStatus("Searching...")
                    Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
                else: # G
                    SetAsssistantStatus("Thinking...")
                    Answer = ChatBot(QueryModifier(Merged_query), chat_history)

                overall_answer_parts.append(Answer)
                UpdateChatLog(Query, Answer) # Log the original query and the final answer

        # Handle exit command
        if 'exit' in Decision:
            os._exit(1)

        # Combine all parts of the answer
        final_answer = ". ".join(filter(None, overall_answer_parts)) # Join parts, filter out empty strings
        
        if final_answer:
            ShowTextToScreen(f"{Assistantname}: {final_answer}")
            SetAsssistantStatus("Answering...")
            TextToSpeech(final_answer)
        elif not is_automation_command and not G and not R:
            # Fallback if no specific command was recognized or produced an output
            fallback_message = "I couldn't quite understand that, or the command didn't produce a specific spoken output."
            ShowTextToScreen(f"{Assistantname}: {fallback_message}")
            SetAsssistantStatus("Available...")
            TextToSpeech(fallback_message)
        
    except Exception as e:
        print(f"Error in MainExecution: {e}")
        SetAsssistantStatus("Error Occurred.")
        TextToSpeech("An error occurred during processing.")
    finally:
        if 'exit' not in Decision: # Ensure status resets unless exiting
            SetAsssistantStatus("Available...")


# ... (rest of your code, FirstThread, SecondThread, if __name__ == "__main__") ...