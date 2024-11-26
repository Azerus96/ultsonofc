import pytest
from app.game.game import Game, GameState
from app.game.player import Player
from app.game.deck import Card

@pytest.fixture
def game():
    return Game()

@pytest.fixture
def players():
    return [
        Player("player1", "Player 1"),
        Player("player2", "Player 2")
    ]

def test_game_initialization(game):
    assert game.state == GameState.WAITING
    assert game.current_street == 0
    assert game.current_player_id is None

def test_add_players(game, players):
    for player in players:
        game.player_manager.add_player(player)
    assert len(game.player_manager.players) == 2

def test_start_game(game, players):
    # Добавляем игроков
    for player in players:
        game.player_manager.add_player(player)
    
    # Начинаем игру
    game.start_game()
    
    assert game.state == GameState.DEALING
    assert game.current_street == 1
    assert game.current_player_id is not None
    
    # Проверяем начальные карты
    for player in game.player_manager.players.values():
        assert len(player.hand.current_cards) == 5

def test_player_action(game, players):
    # Подготовка игры
    for player in players:
        game.player_manager.add_player(player)
    game.start_game()
    
    player = game.player_manager.get_player(game.current_player_id)
    card = player.hand.current_cards[0]
    
    # Выполняем действие
    action = {
        'type': 'place_card',
        'card': card.to_dict(),
        'position': 'bottom',
        'index': 0
    }
    
    success = game.handle_player_action(game.current_player_id, action)
    assert success
    assert len(player.hand.current_cards) == 4
    assert len(player.hand.bottom) == 1

def test_fantasy_qualification(game, players):
    # Подготовка игры с конкретными картами для фантазии
    for player in players:
        game.player_manager.add_player(player)
    
    player = game.player_manager.get_player(players[0].id)
    
    # Создаем руку с QQ в верхней линии
    player.hand.top = [
        Card('Q', '♥'),
        Card('Q', '♦'),
        Card('K', '♣')
    ]
    player.hand.middle = [
        Card('10', '♥'),
        Card('J', '♥'),
        Card('Q', '♥'),
        Card('K', '♥'),
        Card('A', '♥')
    ]
    player.hand.bottom = [
        Card('2', '♣'),
        Card('2', '♦'),
        Card('2', '♥'),
        Card('3', '♣'),
        Card('3', '♦')
    ]
    
    assert game.check_fantasy()
    assert players[0].id in game.fantasy_players

def test_scoring(game, players):
    # Подготовка игры с конкретными комбинациями
    for player in players:
        game.player_manager.add_player(player)
    
    player1 = game.player_manager.get_player(players[0].id)
    player2 = game.player_manager.get_player(players[1].id)
    
    # Устанавливаем конкретные комбинации
    player1.hand.top = [
        Card('Q', '♥'),
        Card('Q', '♦'),
        Card('K', '♣')
    ]
    player2.hand.top = [
        Card('J', '♥'),
        Card('J', '♦'),
        Card('A', '♣')
    ]
    
    game.end_game()
    
    assert player1.score != 0 or player2.score != 0
