from app import create_app
from app.web.socket import socketio
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Используем переменную PORT, если она есть
    socketio.run(app, host='0.0.0.0', port=port, debug=app.config['DEBUG'])
