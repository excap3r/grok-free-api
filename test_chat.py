import requests
import os
from dotenv import load_dotenv
import time
import signal
import sys
import itertools

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
        sys.exit(0)  # Force exit the program

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
        """Wait for and retrieve the response from the chat with extended timeout and optimized polling."""
        start_time = time.time()
        # Begin with short polling intervals then gradually increase to reduce load
        polling_interval = 0.1  # Start with a very short interval
        max_interval = 1.0      # Maximum polling interval
        
        # Create nice spinner animation for waiting
        spinner = itertools.cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
        
        while time.time() - start_time < timeout and self.running:
            try:
                # Update spinner animation
                print(f"\r{next(spinner)} Waiting for response... ", end="", flush=True)
                
                response = requests.get(
                    f'{self.api_url}/api/v1/response/latest',
                    headers=self.headers
                )
                if response.status_code == 200:
                    # Clear the spinner line
                    print("\r" + " " * 50 + "\r", end="", flush=True)
                    return response.json()['response']
                elif response.status_code == 204:  # No Content - means no new messages
                    # Server has no new messages - continue polling silently
                    time.sleep(1)  # Wait a bit longer before next poll to reduce server load
                    continue
                elif response.status_code == 202:  # Accepted - server is still processing
                    # Continue polling silently - don't try to parse JSON
                    pass
                elif response.status_code != 404:  # If it's an actual error, not just "no response yet"
                    # Only display actual errors, not status updates
                    if response.status_code >= 400:
                        print(f"\r\nServer error: {response.status_code}")
                        # Only try to parse JSON for error responses
                        if response.content and len(response.content.strip()) > 0:
                            try:
                                json_data = response.json()
                                if 'error' in json_data:
                                    print(f"Error: {json_data['error']}")
                            except ValueError as json_err:
                                print(f"Error parsing JSON: {str(json_err)}")
            except requests.exceptions.RequestException as e:
                print(f"\nError getting response: {str(e)}")
                return None
                
            # Adaptive sleep: start short, then gradually increase to avoid hammering the server
            time.sleep(polling_interval)
            # Increase interval for next poll, but cap at max_interval
            polling_interval = min(polling_interval * 1.5, max_interval)
        
        # Clear the spinner line
        print("\r" + " " * 50 + "\r", end="", flush=True)
        print("No response received within timeout.")
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
                        # The get_response method now handles the spinner animation
                        response = self.get_response()
                        if response:
                            print(f"grok-free-api: {response}\n")
                        # get_response handles printing the timeout message
                    else:
                        print("\nFailed to send message\n")
            except EOFError:
                self.running = False
                print('\nGracefully shutting down...')
                break
            except KeyboardInterrupt:
                # Catch Ctrl+C here in case the signal handler doesn't trigger
                self.running = False
                print('\nGracefully shutting down...')
                sys.exit(0)

def main():
    chat = ChatAPI()
    chat.interactive_chat()

if __name__ == "__main__":
    main()