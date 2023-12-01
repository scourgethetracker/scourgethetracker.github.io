#!/usr/bin/env python3

from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
import os

# Load API key from an environment variable for security


# Check if the API key is available
if not openai.api_key:
    raise ValueError("No OpenAI API key found. Set the OPENAI_API_KEY environment variable.")

messages = [{"role": "system", "content": "You are an intelligent assistant."}]

while True:
    message = input("Prompt : ")
    if message:
        messages.append({"role": "user", "content": message})

        try:
            chat = client.chat.completions.create(model="gpt-3.5", messages=messages)
        except Exception as e:
            print(f"Error occurred: {e}")
            continue

        reply = chat.choices[0].message.content
        print(f"ChatGPT: {reply}")
        messages.append({"role": "assistant", "content": reply})
