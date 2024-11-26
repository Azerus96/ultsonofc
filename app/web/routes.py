from flask import Blueprint, render_template, jsonify, request, session
from ..game.game import Game
from ..game.player import Player
import uuid

bp = Blueprint('routes', __name__)
game_instance = Game()

@bp.route('/')
def index():
    """Главная страница"""
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    
    return render_template('index.html', 
                         player_id=session['player_id'],
                         game_state=game_instance.get_game_state())

@bp.route('/join', methods=['POST'])
def join_game():
    """Присоединение к игре"""
    data = request.get_json()
    player_id = session.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'No session found'}), 400
        
    player = Player(
        player_id=player_id,
        name=data.get('name', f'Player_{player_id[:6]}'),
        is_ai=False
    )
    
    game_instance.player_manager.add_player(player)
    return jsonify({'status': 'success', 'player_id': player_id})

@bp.route('/start', methods=['POST'])
def start_game():
    """Начало игры"""
    try:
        game_instance.start_game()
        return jsonify({'status': 'success'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/action', methods=['POST'])
def player_action():
    """Обработка действия игрока"""
    player_id = session.get('player_id')
    if not player_id:
        return jsonify({'error': 'No session found'}), 400
        
    data = request.get_json()
    success = game_instance.handle_player_action(player_id, data)
    
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Invalid action'}), 400

@bp.route('/state')
def get_state():
    """Получение текущего состояния игры"""
    return jsonify(game_instance.get_game_state())
