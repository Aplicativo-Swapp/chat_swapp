from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

class ChatManager:
    def __init__(self):
        self.conversations = {}
    
    def send_message(self, sender_id, receiver_id, message_text):
        participants = frozenset({sender_id, receiver_id})
        
        if participants not in self.conversations:
            self.conversations[participants] = []
        
        message = {
            'sender': sender_id,
            'receiver': receiver_id,
            'message': message_text,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.conversations[participants].append(message)
    
    def get_chat_history(self, user1, user2):
        participants = frozenset({user1, user2})
        return sorted(self.conversations.get(participants, []), key=lambda x: x['timestamp'])

chat_manager = ChatManager()

@app.route('/send_message', methods=['POST'])
def api_send_message():
    data = request.json
    chat_manager.send_message(
        data['sender_id'],
        data['receiver_id'],
        data['message']
    )
    return jsonify({'status': 'success'}), 200

@app.route('/get_chat_history', methods=['GET'])
def api_get_chat_history():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    history = chat_manager.get_chat_history(user1, user2)
    return jsonify(history), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)