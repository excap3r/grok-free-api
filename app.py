# Constants for response handling
RESPONSE_EXPIRATION_TIME = 300  # 5 minutes in seconds
# Rate limiting has been removed as per user request

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from queue import Queue
from threading import Lock
import time
import uuid

app = Flask(__name__)
# Apply CORS to all routes including OpenAI-compatible endpoints
CORS(app)

# Message queue and response storage
message_queue = Queue()
response_storage = {
    'responses': [],
    'max_responses': 10,
    'timestamp': time.time(),
    'last_retrieved_index': -1  # Track the index of last retrieved response instead of storing all responses
}
processed_messages = set()
response_lock = Lock()
processed_lock = Lock()


# Rate limiting function has been removed

@app.route('/api/v1/chat', methods=['POST'])
def chat():
    try:
        # Rate limiting has been removed
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        # Check if message was already processed
        with processed_lock:
            if message in processed_messages:
                return jsonify({
                    'error': 'Message already processed'
                }), 400
        
        # Add message to queue and mark as processed
        message_queue.put(message)
        with processed_lock:
            processed_messages.add(message)
        
        return jsonify({
            'success': True,
            'message': 'Message queued successfully'
        })
    except Exception as e:
        app.logger.error(f'Error in chat endpoint: {str(e)}')
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/v1/response/latest', methods=['GET'])
def get_last_response():
    try:
        # Improved response retrieval logic
        current_time = time.time()
        
        with response_lock:
            if not response_storage['responses']:
                # Return 202 Accepted instead of 404 to indicate the request is valid but processing
                # This avoids flooding logs with 404 errors during normal polling
                return jsonify({
                    'status': 'pending',
                    'message': 'The response is being processed. Please try again in a moment.'
                }), 202
            
            # Get the next newest response that hasn't been retrieved yet
            # Check if there are any new responses since the last retrieval
            current_response_count = len(response_storage['responses'])
            last_retrieved = response_storage['last_retrieved_index']
            
            # If there's a newer response available, send it
            if current_response_count > 0 and last_retrieved < current_response_count - 1:
                # Get the next response in sequence
                next_index = last_retrieved + 1
                next_response = response_storage['responses'][next_index]
                
                # Update the last retrieved index
                response_storage['last_retrieved_index'] = next_index
                
                # Return the response
                return jsonify({
                    'status': 'ready',
                    'response': next_response['response'],
                    'timestamp': next_response['timestamp'],
                    'response_index': next_index,
                    'total_responses': current_response_count
                })
            
            # If we've already sent all available responses
            if response_storage['responses']:
                # Just indicate there's nothing new, but don't resend old content
                return jsonify({
                    'status': 'no_new_responses',
                    'message': 'All available responses have been retrieved',
                    'last_retrieved_index': last_retrieved,
                    'total_responses': current_response_count
                }), 204  # 204 No Content is more appropriate here
            
            # No responses at all
            return jsonify({
                'status': 'empty',
                'error': 'No responses available',
                'message': 'No responses have been generated yet.'
            }), 404
            
    except Exception as e:
        app.logger.error(f'Error in get_last_response endpoint: {str(e)}')
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'An error occurred while retrieving the response'
        }), 500

@app.route('/api/v1/messages/pending', methods=['GET'])
def get_pending_message():
    try:
        # Rate limiting has been removed
        if not message_queue.empty():
            message = message_queue.get()
            return jsonify({
                'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': '1',
                'choices': [
                    {
                        'index': 0,
                        'message': {
                            'role': 'user',
                            'content': message
                        },
                        'finish_reason': None
                    }
                ]
            })
        return jsonify({
            'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': '1',
            'choices': []
        })
    except Exception as e:
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

@app.route('/api/v1/chat/completions/latest', methods=['GET'])
def get_latest_completion():
    try:
        # Rate limiting has been removed
        if not message_queue.empty():
            message = message_queue.get()
            return jsonify({
                'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': '1',
                'choices': [
                    {
                        'index': 0,
                        'message': {
                            'role': 'user',
                            'content': message
                        },
                        'finish_reason': None
                    }
                ]
            })
        return jsonify({
            'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': '1',
            'choices': []
        })
    except Exception as e:
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

# Standard OpenAI compatibility endpoints
@app.route('/v1/models', methods=['GET'])
def list_models():
    """OpenAI-compatible models listing endpoint"""
    # Return a simplified list of models for compatibility
    return jsonify({
        'object': 'list',
        'data': [
            {
                'id': '2',
                'object': 'model',
                'created': int(time.time()) - 10000,
                'owned_by': 'grok.example.com'
            },
            {
                'id': '3',
                'object': 'model',
                'created': int(time.time()) - 5000,
                'owned_by': 'grok.example.com'
            }
        ]
    })

@app.route('/v1/chat/completions', methods=['POST'])
def openai_chat_completions(from_api_route=False):
    """OpenAI-compatible chat completions endpoint"""
    try:
        if request.is_json:
            data = request.get_json()
            # Log incoming request data for debugging
            app.logger.info(f"Received OpenAI-compatible request with data: {data}")
            stream_mode = data.get('stream', False)
            
            # Check if this is a typical OpenAI request with messages
            if 'messages' in data:
                # Extract the last user message
                user_messages = [msg for msg in data['messages'] if msg.get('role') == 'user']
                if user_messages:
                    last_message = user_messages[-1]['content']
                    # Queue the message
                    message_queue.put(last_message)
                    with processed_lock:
                        processed_messages.add(last_message)
                    
                    # Handle streaming mode differently if requested
                    if stream_mode:
                        # For simplicity, we're not implementing true streaming
                        # Just return a compatible format
                        response_id = f'chatcmpl-{str(uuid.uuid4())[:8]}'
                        return jsonify({
                            'id': response_id,
                            'object': 'chat.completion.chunk',
                            'created': int(time.time()),
                            'model': data.get('model', 'gpt-3.5-turbo'),
                            'choices': [
                                {
                                    'index': 0,
                                    'delta': {
                                        'role': 'assistant',
                                        'content': 'Message received and queued for processing'
                                    },
                                    'finish_reason': 'stop'
                                }
                            ]
                        })
                    else:
                        # Return a compatible response format for non-streaming
                        return jsonify({
                            'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
                            'object': 'chat.completion',
                            'created': int(time.time()),
                            'model': data.get('model', 'gpt-3.5-turbo'),
                            'choices': [
                                {
                                    'index': 0,
                                    'message': {
                                        'role': 'assistant',
                                        'content': 'Message received and queued for processing'
                                    },
                                    'finish_reason': 'stop'
                                }
                            ]
                        })
        
        # If we get here, the request wasn't in the expected format
        return jsonify({
            'error': {
                'message': 'Invalid request format',
                'type': 'invalid_request_error'
            }
        }), 400
    except Exception as e:
        app.logger.error(f'Error in openai_chat_completions endpoint: {str(e)}')
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

@app.route('/api/v1/chat/completions', methods=['POST'])
def store_response():
    """
    Compatibility endpoint that supports both the original custom format 
    and the OpenAI-compatible format for storing chat completions.
    """
    try:
        if not request.is_json:
            return jsonify({'error': {'message': 'Content-Type must be application/json', 'type': 'invalid_request_error'}}), 415

        data = request.get_json()
        
        # Check if this is an OpenAI-format request
        if 'messages' in data:
            # This is an OpenAI-format request, redirect to the OpenAI handler
            return openai_chat_completions()
        
        # Original custom format handling
        if not data or 'response' not in data:
            return jsonify({
                'error': {
                    'message': 'Response is required',
                    'type': 'invalid_request_error'
                }
            }), 400
        
        current_time = time.time()
        with response_lock:
            # Add new response with timestamp
            new_response = {
                'response': data['response'],
                'timestamp': current_time
            }
            response_storage['responses'].append(new_response)
            response_storage['timestamp'] = current_time
            
            # Keep only the last N responses
            if len(response_storage['responses']) > response_storage['max_responses']:
                response_storage['responses'] = response_storage['responses'][-response_storage['max_responses']:]
        
        return jsonify({
            'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': '1',
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': 'Response stored successfully'
                    },
                    'finish_reason': 'stop'
                }
            ]
        })
    except Exception as e:
        app.logger.error(f'Error in store_response endpoint: {str(e)}')
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

@app.route('/api/v1/messages/mark-processed', methods=['POST'])
def mark_messages_processed():
    """Endpoint to mark messages as processed to avoid duplicates"""
    try:
        # Accept any JSON payload or even empty requests
        # This makes the endpoint more compatible with different client implementations
        if request.is_json:
            data = request.get_json()
            app.logger.info(f"Received mark-processed request with data: {data}")
        else:
            app.logger.info("Received mark-processed request with no JSON data")
            
        # Always return success - we just need to acknowledge the client
        # No validation required for this simple implementation
        return jsonify({
            'success': True,
            'message': 'Message acknowledged'
        })
    except Exception as e:
        app.logger.error(f'Error in mark_messages_processed endpoint: {str(e)}')
        return jsonify({
            'error': str(e)
        }), 500

# Add basic health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'message': 'grok.example.com server is running'
    })

if __name__ == '__main__':
    print("Starting grok.example.com server on http://localhost:5001")
    print("OpenAI-compatible endpoints available at:")
    print("  - http://localhost:5001/v1/models")
    print("  - http://localhost:5001/v1/chat/completions")
    app.run(host='0.0.0.0', port=5001, debug=True)