import socketio
import time

# Configurações
SERVER_URL = "http://localhost:5000"
USER_ID = "user2"  # Altere para cada instância

sio = socketio.Client()

@sio.event
def connect():
    print("\nConectado ao servidor!")
    sio.emit('register_user', USER_ID)
    print(f"Registrado como: {USER_ID}")

@sio.event
def private_message(data):
    print(f"\n[NOVA MENSAGEM] De {data['from']}: {data['message']}")

@sio.event
def message_status(data):
    print(f"\n[STATUS] Mensagem para {data['to']}: {data['status']}")

def send_message():
    while True:
        recipient = input("\nDestinatário: ")
        message = input("Mensagem: ")
        sio.emit('private_message', {
            'to': recipient,
            'message': message,
            'from': USER_ID
        })

if __name__ == '__main__':
    sio.connect(SERVER_URL)
    try:
        send_message()
    except KeyboardInterrupt:
        sio.disconnect()