# Custom Grok API Example 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

A local API server that provides OpenAI-compatible chat completions API for your preferred Grok interface, enabling seamless integration with your applications.

## 🌟 Features

- 🔄 OpenAI-compatible API endpoints
- 🔄 Message processing with automatic queueing
- 📋 Clean API versioning
- 🔌 Easy integration with browser extension
- 🚀 Fast and reliable message processing

## 🛠️ Installation

### Prerequisites

- Python 3.13 or higher
- pip (Python package installer)
- A modern web browser
- Tampermonkey or similar userscript manager

### Server Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/grok-api.git
   cd grok-api
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
   
   You may also need to install additional packages for the test client:
   ```bash
   pip3 install requests python-dotenv colorama
   ```

3. Start the local server:
   ```bash
   python3 app.py
   ```
   The server will start on `http://localhost:5001`

### Browser Extension Setup

1. Install the Tampermonkey browser extension:
   - [Chrome Web Store](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
   - [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)

2. Create a new userscript in Tampermonkey:
   - Click on the Tampermonkey icon
   - Select "Create a new script"
   - Copy the contents of `chat.user.js` into the editor
   - Save the script (Ctrl+S or ⌘+S)

3. Enable the script and navigate to your Grok URL

> **IMPORTANT:** You need to replace `grok.example.com` with your actual Grok URL in the following files:
> - In `chat.user.js`: Update the `@match` pattern (line 7) and the `Origin` header (line 33)
> - In `app.py`: Update references to the domain in server messages (lines 404-405) 
> - The model ownership field uses a hyphenated format (`grok-example`)
> - In any other files that reference this domain
>
> It's crucial that your Grok URL is correctly set before using the script, otherwise the userscript won't activate on the correct page.

## 🔧 Configuration

The server comes with sensible defaults, but you can customize:
- `RESPONSE_EXPIRATION_TIME`: How long to keep responses (default: 300 seconds)
- `API_BASE`: API endpoint base URL (default: http://localhost:5001)

## 📡 API Endpoints

### Send a Message

```http
POST /api/v1/chat
Content-Type: application/json

{
    "message": "Your message here"
}
```

### Chat Completion

```http
POST /api/v1/chat/completions
Content-Type: application/json

{
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
}
```

### Get Latest Completion

```http
GET /api/v1/chat/completions/latest
```

Returns the latest chat completion response in OpenAI format.

### Get Pending Messages

```http
GET /api/v1/messages/pending
```

### Mark Message as Processed

```http
POST /api/v1/messages/mark-processed
Content-Type: application/json

{
    "message": "Message content to mark as processed"
}
```

## 📊 Message Queue System

The API implements a message queuing system that ensures all requests are processed in an orderly manner. Messages are stored until they are processed, preventing duplicates and ensuring a smooth experience.

## 📝 Response Format

All responses follow the OpenAI Chat Completions API format. Note that the model IDs have been changed to numeric values (2 and 3) instead of the OpenAI model names, and ownership is set to 'grok-example':

```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "2", // Model ID 2 or 3
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Response content here"
            },
            "finish_reason": "stop"
        }
    ]
}
```

## 🧪 Testing

A test client is included to help you verify that your setup is working properly:

```bash
python3 test_chat.py
```

This will start an interactive chat session where you can test the functionality of the API.

## 🗲 Model IDs and Ownership

The API uses simplified model IDs:

- `2` - Equivalent to what was previously labeled as gpt-3.5-turbo
- `3` - Equivalent to what was previously labeled as gpt-4o

Model ownership is set to `grok-example`. You can modify these values in the `list_models` function in `app.py` if needed.

## 🔍 Troubleshooting

### Common Issues

1. **Server Connection Error**
   - Ensure the local server is running
   - Check if the port 5001 is available
   - Verify your firewall settings

2. **Userscript Not Working**
   - Ensure Tampermonkey is properly installed
   - Check if the script is enabled
   - Clear browser cache and reload the page
   - Verify that you've updated all instances of `grok.example.com` to your actual Grok URL

3. **Processing Issues**
   - Ensure your messages are properly formatted
   - Check for server connectivity
   - Verify your browser's console for error messages

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 🛠️ Quick URL Replacement

To quickly replace all instances of `grok.example.com` with your actual Grok URL, you can use this command (replacing `your-grok-url.com` with your actual URL). Note that this won't update the hyphenated format in model ownership:

```bash
find . -type f -name "*.py" -o -name "*.js" -o -name "*.md" | xargs sed -i '' 's/grok\.example\.com/your-grok-url.com/g'

# For manually updating the model ownership format if needed:
sed -i '' 's/grok-example/your-custom-name/g' app.py
```

> Note: This command works for macOS. For Linux, remove the `''` after `-i`.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by OpenAI's API design
- Built with Flask and Python