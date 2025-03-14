import requests
import os
from dotenv import load_dotenv
import time
import signal
import sys

class ChatAPI:
    def __init__(self):
        load_dotenv()
        self.api_url = 'http://localhost:5001'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print('\nGracefully shutting down...')
        self.running = False

    def send_message(self, message):
        """Send a message through the local API server without limitations."""
        try:
            response = requests.post(
                f'{self.api_url}/api/v1/chat',
                json={'message': message},
                headers=self.headers
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"\nError sending message: {str(e)}")
            if e.response:
                print(f"Status code: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            return False

    def get_response(self, timeout=300):
        """Wait for and retrieve the response from the chat with extended timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout and self.running:
            try:
                response = requests.get(
                    f'{self.api_url}/api/v1/response/latest',
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()['response']
            except requests.exceptions.RequestException as e:
                print(f"\nError getting response: {str(e)}")
                return None
            time.sleep(0.5)
        return None

    def interactive_chat(self):
        """Start an interactive chat session."""
        print("Welcome to grok-free-api Chat! (Press Ctrl+C to exit)")
        print("Type your messages and press Enter to send.\n")

        while self.running:
            try:
                message = input("> ")
                if message.strip():
                    print("Sending message...")
                    if self.send_message(message):
                        print("Waiting for response...")
                        response = self.get_response()
                        if response:
                            print(f"\grok-free-api: {response}\n")
                        else:
                            print("\nNo response received within timeout\n")
                    else:
                        print("\nFailed to send message\n")
            except EOFError:
                break

def main():
    chat = ChatAPI()
    chat.interactive_chat()

if __name__ == "__main__":
    main()