#!/usr/bin/env python3
import openai
import os

def read_file_contents(file_path):
    try:
        with open(file_path, 'r') as file:
            return True, file.read()  # Return a tuple (success, content)
    except Exception as e:
        return False, f"Error reading file '{file_path}': {e}"

def aggregate_directory_contents(directory, ignored_extensions, ignored_directories):
    all_contents = ""
    error_files = []

    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if d not in ignored_directories]
        for file in files:
            if any(file.endswith(ext) for ext in ignored_extensions):
                continue  # Skip files with ignored extensions

            file_path = os.path.join(root, file)
            success, file_content = read_file_contents(file_path)
            if success:
                all_contents += f"\nFile: {file}\n{file_content}"
            else:
                error_files.append(file_content)

    return all_contents, error_files

# List of ignored file extensions
ignored_extensions = ['.pcy', '.pyc', '.exe', '.so', '.gz', '.tar', '.zip', '.ico', '.jpg', '.gif', '.jpeg', '.tiff', '.png']

# List of ignored directories
ignored_directories = ['.git', 'site-packages', 'docs', 'bin']

# Load API key from an environment variable for security
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5')

if not openai.api_key:
    raise ValueError("No OpenAI API key found. Set the OPENAI_API_KEY environment variable.")

# Initialize the conversation with the system message
messages = [{"role": "system", "content": "You are an intelligent assistant specialized in Python development."}]

# Get directory from the user
directory = input("Enter the directory path: ")

# Aggregate contents of all files in the directory and subdirectories, ignoring specified extensions and directories
directory_contents, error_files = aggregate_directory_contents(directory, ignored_extensions, ignored_directories)

# Add the aggregated content as a system message for context
messages.append({"role": "system", "content": f"Python Codebase contents:\n{directory_contents}"})

# Print error messages for files that couldn't be read
for error in error_files:
    print(error)

while True:
    message = input("Python Development Prompt : ")
    if message:
        messages.append({"role": "user", "content": message})

        try:
            response = openai.ChatCompletion.create(
                model=openai_model,
                messages=messages
            )
            reply = response.choices[0].message['content']
        except Exception as e:
            print(f"Error occurred: {e}")
            continue

        print(f"ChatGPT: {reply}")
        messages.append({"role": "assistant", "content": reply})
