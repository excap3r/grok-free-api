# Grok Chat API Integration

A local API server that provides OpenAI-compatible chat completions API for Grok.

## Features

- OpenAI-compatible API endpoints
- Rate limiting to prevent API abuse
- Automatic message queueing
- Clean API versioning

## Setup

### Userscript Setup

1. Install a userscript manager (like Tampermonkey) in your browser
2. Create a new userscript and copy the contents of `chat.user.js`
3. Enable the script and navigate to Grok chat

## API Endpoints

### Chat Completion

POST `/api/v1/chat/completions`
```json
{
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
}
```

### Get Latest Completion

GET `/api/v1/chat/completions/latest`

Returns the latest chat completion response in OpenAI format.

### Get Pending Messages

GET `/api/v1/messages/pending`

Returns any pending messages that need to be processed.

### Mark Message as Processed

POST `/api/v1/messages/mark-processed`
```json
{
    "message": "Message content to mark as processed"
}
```

## Rate Limiting

The API implements a simple rate limiting mechanism with a 1-second delay between requests to prevent abuse.

## Response Format

All responses follow the OpenAI Chat Completions API format:

```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "grok-1",
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