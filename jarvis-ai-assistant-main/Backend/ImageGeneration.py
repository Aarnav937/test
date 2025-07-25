import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep
import json

# Set API URL and headers
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}

# Ensure the Data folder exists
if not os.path.exists("Data"):
    os.makedirs("Data")

def open_images(prompt):
    folder_path = r"Data"
    prompt = prompt.replace(" ", "_")
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)

        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)

        except IOError:
            print(f"Unable to open {image_path}. Ensure the image file exists and is valid.")

# FIX: Upgraded error handling for more specific feedback.
async def query(payload):
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()  # Raise an error for bad status codes (4xx or 5xx)
        return response.content
    except requests.exceptions.HTTPError as e:
        # Provide more specific error info from the API
        print(f"HTTP Error: {e.response.status_code}. Response: {e.response.text}")
        return e.response.content # Return error content for further inspection
    except requests.exceptions.RequestException as e:
        print(f"Error querying API: {e}")
        return None

# FIX: Correctly handles the raw image data from the API.
async def generate_images(prompt: str):
    tasks = []
    print("Submitting 4 image generation requests to the API...")
    for i in range(4):
        seed = randint(0, 1000000)
        payload = {
            "inputs": f"{prompt}, 4k, sharp, high quality, seed={seed}"
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    # Wait for all API calls to complete
    responses = await asyncio.gather(*tasks)
    print("Processing API responses...")

    for i, image_bytes in enumerate(responses):
        if image_bytes:
            # Try to open the response as an image. If it fails, it's likely an error message.
            try:
                # The successful response is raw image data, not JSON
                with open(fr"Data\{prompt.replace(' ', '_')}{i + 1}.jpg", "wb") as f:
                    f.write(image_bytes)
                print(f"Successfully saved Image {i + 1}")

            except Exception as e:
                # If writing bytes fails, it's likely an error response from the API (which is often JSON)
                print(f"Could not save Image {i + 1}. Attempting to decode error message...")
                try:
                    error_message = json.loads(image_bytes.decode('utf-8'))
                    print(f"API Error for Image {i + 1}: {error_message.get('error', 'Unknown error')}")
                    # This can happen if the model is loading
                    if "is currently loading" in str(error_message):
                        print("The model is loading. Please wait a moment and try again.")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    print(f"Could not decode the API error message for Image {i + 1}.")

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# Main execution loop
while True:
    try:
        with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
            data = str(f.read())

        prompt, status = data.split(",")
        status = status.strip()

        if status.lower() == "true":
            print("Status is true. Initiating image generation...")
            GenerateImages(prompt=prompt)

            with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                f.write("False, False")
            print("Image generation complete. Resetting status.")
            break
        else:
            sleep(1)

    # FIX: Catches specific exceptions to avoid hiding bugs.
    except FileNotFoundError:
        print("Waiting for ImageGeneration.data file to be created...")
        sleep(2)
    except ValueError:
        # This can happen if the file is empty or being written to
        sleep(1)
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")
        sleep(1)