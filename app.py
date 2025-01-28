from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os

# Configuração inicial
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///chat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização de extensões
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Modelo de dados para mensagens
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Dicionário para usuários online
active_users = {}

# Criação do banco de dados (executar apenas uma vez)
with app.app_context():
    db.create_all()

# Handlers de Socket.IO
@socketio.on('connect')
def handle_connect():
    print(f'Cliente conectado: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    user_id = next((uid for uid, sid in active_users.items() if sid == request.sid), None)
    if user_id:
        del active_users[user_id]
    print(f'Cliente desconectado: {request.sid}')

@socketio.on('register_user')
def handle_register(user_id):
    active_users[user_id] = request.sid
    print(f'Usuário registrado: {user_id}')

@socketio.on('private_message')
def handle_private_message(data):
    try:
        # Salva no banco de dados
        new_message = Message(
            sender=data['from'],
            receiver=data['to'],
            content=data['message']
        )
        db.session.add(new_message)
        db.session.commit()

        # Encaminha a mensagem
        recipient_sid = active_users.get(data['to'])
        if recipient_sid:
            socketio.emit('private_message', {
                'from': data['from'],
                'message': data['message'],
                'timestamp': new_message.timestamp.isoformat()
            }, to=recipient_sid)

        # Confirmação para o remetente
        socketio.emit('message_status', {
            'status': 'entregue',
            'to': data['to'],
            'timestamp': new_message.timestamp.isoformat()
        }, to=active_users[data['from']])

    except Exception as e:
        print(f'Erro ao processar mensagem: {str(e)}')

# Rotas HTTP
@app.route('/messages/<user_id>/<other_user_id>', methods=['GET'])
def get_messages(user_id, other_user_id):
    try:
        messages = Message.query.filter(
            ((Message.sender == user_id) & (Message.receiver == other_user_id)) |
            ((Message.sender == other_user_id) & (Message.receiver == user_id))
        ).order_by(Message.timestamp.asc()).all()

        return jsonify([{
            'id': msg.id,
            'from': msg.sender,
            'to': msg.receiver,
            'message': msg.content,
            'timestamp': msg.timestamp.isoformat()
        } for msg in messages]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)