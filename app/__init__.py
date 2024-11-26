from flask import Flask
from flask_socketio import SocketIO
import os

socketio = SocketIO()

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        # Загружаем конфигурацию из переменных окружения
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            AI_PROGRESS_TOKEN=os.environ.get('AI_PROGRESS_TOKEN'),
            DEBUG=os.environ.get('FLASK_DEBUG', '0') == '1'
        )
    else:
        app.config.update(test_config)

    # Убеждаемся, что директория для прогресса ИИ существует
    os.makedirs('progress', exist_ok=True)

    # Регистрируем blueprints
    from .web.routes import bp
    app.register_blueprint(bp)

    # Инициализируем Socket.IO
    socketio.init_app(app)

    return app
