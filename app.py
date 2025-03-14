# Constants for response handling
RESPONSE_EXPIRATION_TIME = 300  # 5 minutes in seconds

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from queue import Queue
from threading import Lock
import time
import uuid

app = Flask(__name__)
CORS(app)

# Message queue and response storage
message_queue = Queue()
response_storage = {
    'responses': [],
    'max_responses': 10,
    'timestamp': time.time(),
    'retrieved_responses': set()
}
processed_messages = set()
response_lock = Lock()
processed_lock = Lock()
last_request_time = 0
RATE_LIMIT_DELAY = 1  # Minimum delay between requests in seconds

def rate_limit():
    global last_request_time
    current_time = time.time()
    time_passed = current_time - last_request_time
    if time_passed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - time_passed)
    last_request_time = time.time()

@app.route('/api/v1/chat', methods=['POST'])
def chat():
    try:
        rate_limit()
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
        current_time = time.time()
        with response_lock:
            if not response_storage['responses']:
                return jsonify({
                    'error': 'No response available'
                }), 404
            
            # Get the most recent response that hasn't been retrieved
            for response in reversed(response_storage['responses']):
                if response['response'] not in response_storage['retrieved_responses']:
                    response_storage['retrieved_responses'].add(response['response'])
                    return jsonify({
                        'response': response['response']
                    })
            
            # If all responses have been retrieved, clear the storage
            response_storage['responses'] = []
            response_storage['retrieved_responses'].clear()
            return jsonify({
                'error': 'No new responses available'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/v1/messages/pending', methods=['GET'])
def get_pending_message():
    try:
        rate_limit()
        if not message_queue.empty():
            message = message_queue.get()
            return jsonify({
                'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'grok-1',
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
            'model': 'grok-1',
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
        rate_limit()
        if not message_queue.empty():
            message = message_queue.get()
            return jsonify({
                'id': f'chatcmpl-{str(uuid.uuid4())[:8]}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'grok-1',
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
            'model': 'grok-1',
            'choices': []
        })
    except Exception as e:
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

@app.route('/api/v1/chat/completions', methods=['POST'])
def store_response():
    try:
        if not request.is_json:
            return jsonify({'error': {'message': 'Content-Type must be application/json', 'type': 'invalid_request_error'}}), 415

        data = request.get_json()
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
            'model': 'grok-1',
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)