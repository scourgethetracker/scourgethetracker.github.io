#!/usr/bin/env python3

import requests
import sys

def send_sms(api_key, phone_number, message):
    url = "https://textbelt.com/text"
    payload = {
        "phone": phone_number,
        "message": message,
        "key": api_key,
    }

    try:
        response = requests.post(url, data=payload)
        response_data = response.json()

        if response_data["success"]:
            print(f"SMS sent successfully to {phone_number}")
        else:
            print(f"Failed to send SMS: {response_data['error']}")

    except requests.RequestException as e:
        print(f"Error sending SMS: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python textbelt.py <api_key> <phone_number> <message>")
        sys.exit(1)

    api_key = sys.argv[1]
    phone_number = sys.argv[2]
    message = sys.argv[3]

    send_sms(api_key, phone_number, message)

