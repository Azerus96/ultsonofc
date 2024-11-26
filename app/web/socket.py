from flask_socketio import emit
from .. import socketio, game_instance  # Импортируем socketio из __init__.py
from flask import request  # Добавляем импорт request

@socketio.on('connect')
def handle_connect():
    """Обработка подключения клиента"""
    emit('game_state', game_instance.get_game_state())

@socketio.on('player_ready')
def handle_player_ready(data):
    """Обработка готовности игрока"""
    player_id = data.get('player_id')
    player = game_instance.player_manager.get_player(player_id)
    
    if player:
        player.is_ready = True
        emit('game_state', game_instance.get_game_state(), broadcast=True)

@socketio.on('place_card')
def handle_place_card(data):
    """Обработка размещения карты"""
    player_id = data.get('player_id')
    card_data = data.get('card')
    position = data.get('position')
    index = data.get('index')
    
    action = {
        'type': 'place_card',
        'card': card_data,
        'position': position,
        'index': index
    }
    
    success = game_instance.handle_player_action(player_id, action)
    if success:
        emit('game_state', game_instance.get_game_state(), broadcast=True)
    else:
        emit('error', {'message': 'Invalid move'}, room=request.sid)

@socketio.on('remove_card')
def handle_remove_card(data):
    """Обработка удаления карты"""
    player_id = data.get('player_id')
    position = data.get('position')
    index = data.get('index')
    
    action = {
        'type': 'remove_card',
        'position': position,
        'index': index
    }
    
    success = game_instance.handle_player_action(player_id, action)
    if success:
        emit('game_state', game_instance.get_game_state(), broadcast=True)
    else:
        emit('error', {'message': 'Invalid move'}, room=request.sid)

@socketio.on('chat_message')
def handle_chat_message(data):
    """Обработка сообщений чата"""
    player_id = data.get('player_id')
    message = data.get('message')
    player = game_instance.player_manager.get_player(player_id)
    
    if player:
        emit('chat_message', {
            'player_name': player.name,
            'message': message
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента"""
    pass
