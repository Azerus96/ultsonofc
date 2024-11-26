from app import create_app
from app.web.socket import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=app.config['DEBUG'])
