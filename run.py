from app import create_app, socketio  # Импортируем socketio из app/__init__.py
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, debug=app.config['DEBUG'])
