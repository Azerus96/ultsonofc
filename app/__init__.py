from flask import Flask
from flask_socketio import SocketIO
from app.game import Game  # Изменен импорт
import os

socketio = SocketIO()
game_instance = Game()  # Создаем экземпляр игры

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            AI_PROGRESS_TOKEN=os.environ.get('AI_PROGRESS_TOKEN'),
            DEBUG=os.environ.get('FLASK_DEBUG', '0') == '1'
        )
    else:
        app.config.update(test_config)

    os.makedirs('progress', exist_ok=True)

    from .web.routes import bp
    app.register_blueprint(bp)

    socketio.init_app(app)

    return app
