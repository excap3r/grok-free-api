# GROK-FREE-API 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

A local API server that provides OpenAI-compatible chat completions API for grok-free-api, enabling seamless integration with your applications.

## 🌟 Features

- 🔄 OpenAI-compatible API endpoints
- 🛡️ Rate limiting to prevent API abuse
- 📬 Automatic message queueing
- 📋 Clean API versioning
- 🔌 Easy integration with browser extension
- 🚀 Fast and reliable message processing

## 🛠️ Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- A modern web browser
- Tampermonkey or similar userscript manager

### Server Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/grok-free-api.git
   cd grok-free-api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the local server:
   ```bash
   python app.py
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

3. Enable the script and navigate to [Grok free api](https://grok-free-api.xyz)

## 🔧 Configuration

The server comes with sensible defaults, but you can customize:

- `RATE_LIMIT_DELAY`: Minimum delay between requests (default: 1 second)
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

## 🔒 Rate Limiting

The API implements rate limiting with a 1-second delay between requests to prevent abuse and ensure stable operation. This helps maintain service quality and prevents server overload.

## 📝 Response Format

All responses follow the OpenAI Chat Completions API format:

```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "1",
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

3. **Rate Limiting Issues**
   - Respect the 1-second delay between requests
   - Check your request frequency

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by OpenAI's API design
- Built with Flask and Python