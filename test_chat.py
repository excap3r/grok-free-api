import requests
import os
from dotenv import load_dotenv
import time
import signal
import sys
import itertools
import readline
import json
from datetime import datetime
from colorama import init, Fore, Style, Back

# Initialize colorama for cross-platform color support
init(autoreset=True)

class ChatAPI:
    def __init__(self):
        load_dotenv()
        self.api_url = 'http://localhost:5001'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.running = True
        self.history = []
        self.command_history_file = os.path.expanduser('~/.chat_history')
        self.chat_log_file = os.path.expanduser('~/.chat_log.json')
        
        # Load command history if available
        self._load_command_history()
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print(f"\n{Fore.YELLOW}Gracefully shutting down...{Style.RESET_ALL}")
        self._save_chat_log()  # Save chat log before exiting
        self.running = False
        sys.exit(0)  # Force exit the program
        
    def _load_command_history(self):
        """Load command history from file for up/down arrow navigation."""
        try:
            if os.path.exists(self.command_history_file):
                readline.read_history_file(self.command_history_file)
                readline.set_history_length(100)  # Limit history size
        except Exception as e:
            # Silently fail if history can't be loaded
            pass
    
    def _save_command_history(self):
        """Save command history to file."""
        try:
            readline.write_history_file(self.command_history_file)
        except Exception as e:
            # Silently fail if history can't be saved
            pass
            
    def _save_chat_log(self):
        """Save the current chat session to a JSON file."""
        try:
            if self.history:
                # Create a chat log with timestamp
                chat_log = {
                    'timestamp': datetime.now().isoformat(),
                    'conversations': self.history
                }
                
                # Load existing logs if any
                existing_logs = []
                if os.path.exists(self.chat_log_file):
                    try:
                        with open(self.chat_log_file, 'r') as f:
                            existing_logs = json.load(f)
                    except json.JSONDecodeError:
                        existing_logs = []
                
                # Append this session and save
                if not isinstance(existing_logs, list):
                    existing_logs = []
                existing_logs.append(chat_log)
                
                with open(self.chat_log_file, 'w') as f:
                    json.dump(existing_logs, f, indent=2)
        except Exception as e:
            # Silently fail if log can't be saved
            pass

    def send_message(self, message):
        """Send a message through the local API server without limitations."""
        try:
            # Add to history before sending
            self.history.append({'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()})
            
            response = requests.post(
                f'{self.api_url}/api/v1/chat',
                json={'message': message},
                headers=self.headers
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"\n{Fore.RED}Error sending message: {str(e)}{Style.RESET_ALL}")
            if e.response:
                print(f"{Fore.RED}Status code: {e.response.status_code}{Style.RESET_ALL}")
                print(f"{Fore.RED}Response content: {e.response.text}{Style.RESET_ALL}")
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
                # Update spinner animation with color
                print(f"\r{Fore.CYAN}{next(spinner)} Waiting for response... {Style.RESET_ALL}", end="", flush=True)
                
                response = requests.get(
                    f'{self.api_url}/api/v1/response/latest',
                    headers=self.headers
                )
                if response.status_code == 200:
                    # Clear the spinner line
                    print("\r" + " " * 50 + "\r", end="", flush=True)
                    response_text = response.json()['response']
                    
                    # Add to chat history
                    self.history.append({'role': 'assistant', 'content': response_text, 'timestamp': datetime.now().isoformat()})
                    
                    return response_text
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
                        print(f"\r\n{Fore.RED}Server error: {response.status_code}{Style.RESET_ALL}")
                        # Only try to parse JSON for error responses
                        if response.content and len(response.content.strip()) > 0:
                            try:
                                json_data = response.json()
                                if 'error' in json_data:
                                    print(f"{Fore.RED}Error: {json_data['error']}{Style.RESET_ALL}")
                            except ValueError as json_err:
                                print(f"{Fore.RED}Error parsing JSON: {str(json_err)}{Style.RESET_ALL}")
            except requests.exceptions.RequestException as e:
                print(f"\n{Fore.RED}Error getting response: {str(e)}{Style.RESET_ALL}")
                return None
                
            # Adaptive sleep: start short, then gradually increase to avoid hammering the server
            time.sleep(polling_interval)
            # Increase interval for next poll, but cap at max_interval
            polling_interval = min(polling_interval * 1.5, max_interval)
        
        # Clear the spinner line
        print("\r" + " " * 50 + "\r", end="", flush=True)
        print(f"{Fore.YELLOW}No response received within timeout.{Style.RESET_ALL}")
        return None

    def interactive_chat(self):
        """Start an interactive chat session."""
        print(f"{Fore.GREEN}╔═════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.GREEN}║ {Fore.CYAN}Welcome to grok-free-api Chat!{Fore.GREEN}                ║{Style.RESET_ALL}")
        print(f"{Fore.GREEN}║ {Style.DIM}Type your messages and press Enter to send{Fore.GREEN}    ║{Style.RESET_ALL}")
        print(f"{Fore.GREEN}║ {Style.DIM}Use /help to see available commands{Fore.GREEN}         ║{Style.RESET_ALL}")
        print(f"{Fore.GREEN}╚═════════════════════════════════════════════╝{Style.RESET_ALL}\n")

        while self.running:
            try:
                message = input(f"{Fore.GREEN}>{Style.RESET_ALL} ")
                
                # Skip empty messages
                if not message.strip():
                    continue
                    
                # Process commands starting with /
                if message.startswith('/'):
                    self._process_command(message[1:])
                    continue
                
                # Skip the echo since the input line already shows what the user typed
                # Send regular message
                print(f"{Fore.YELLOW}Sending message...{Style.RESET_ALL}")
                if self.send_message(message):
                    # The get_response method now handles the spinner animation
                    response = self.get_response()
                    if response:
                        print(f"{Fore.GREEN}AI:{Style.RESET_ALL} {response}\n")
                    # get_response handles printing the timeout message
                else:
                    print(f"\n{Fore.RED}Failed to send message{Style.RESET_ALL}\n")
                    
                # Save command history
                self._save_command_history()
            except EOFError:
                self.running = False
                print(f"\n{Fore.YELLOW}Gracefully shutting down...{Style.RESET_ALL}")
                self._save_chat_log()  # Save chat log before exiting
                break
            except KeyboardInterrupt:
                # Catch Ctrl+C here in case the signal handler doesn't trigger
                self.running = False
                print(f"\n{Fore.YELLOW}Gracefully shutting down...{Style.RESET_ALL}")
                self._save_chat_log()  # Save chat log before exiting
                sys.exit(0)
                
    def _process_command(self, command):
        """Process chat commands that start with a slash."""
        cmd = command.lower().strip()
        
        if cmd == 'help' or cmd == '?':
            print(f"\n{Fore.CYAN}Available commands:{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}/help{Style.RESET_ALL} - Show this help message")
            print(f"  {Fore.GREEN}/clear{Style.RESET_ALL} - Clear the screen")
            print(f"  {Fore.GREEN}/exit{Style.RESET_ALL} - Exit the chat")
            print(f"  {Fore.GREEN}/save{Style.RESET_ALL} - Save chat history to file")
            print(f"  {Fore.GREEN}/models{Style.RESET_ALL} - Show available models")
            print(f"  {Fore.GREEN}/health{Style.RESET_ALL} - Check API health\n")
            
        elif cmd == 'clear' or cmd == 'cls':
            os.system('cls' if os.name == 'nt' else 'clear')
            
        elif cmd == 'exit' or cmd == 'quit':
            print(f"\n{Fore.YELLOW}Exiting chat...{Style.RESET_ALL}")
            self._save_chat_log()
            self.running = False
            sys.exit(0)
            
        elif cmd == 'save':
            self._save_chat_log()
            print(f"\n{Fore.GREEN}Chat history saved to {self.chat_log_file}{Style.RESET_ALL}\n")
            
        elif cmd == 'models':
            try:
                response = requests.get(f'{self.api_url}/v1/models', headers=self.headers)
                if response.status_code == 200:
                    models = response.json().get('data', [])
                    print(f"\n{Fore.CYAN}Available models:{Style.RESET_ALL}")
                    for model in models:
                        print(f"  {Fore.GREEN}{model['id']}{Style.RESET_ALL} - {model.get('owned_by', 'Unknown')}")
                    print()
                else:
                    print(f"\n{Fore.RED}Failed to retrieve models: {response.status_code}{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"\n{Fore.RED}Error retrieving models: {str(e)}{Style.RESET_ALL}\n")
                
        elif cmd == 'health':
            try:
                response = requests.get(f'{self.api_url}/health', headers=self.headers)
                if response.status_code == 200:
                    print(f"\n{Fore.GREEN}API health check: OK{Style.RESET_ALL}\n")
                else:
                    print(f"\n{Fore.RED}API health check failed: {response.status_code}{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"\n{Fore.RED}API health check error: {str(e)}{Style.RESET_ALL}\n")
                
        else:
            print(f"\n{Fore.YELLOW}Unknown command: {command}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Type /help to see available commands{Style.RESET_ALL}\n")

def main():
    chat = ChatAPI()
    chat.interactive_chat()

if __name__ == "__main__":
    main()