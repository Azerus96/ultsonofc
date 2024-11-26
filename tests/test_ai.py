import pytest
import numpy as np
from app.ai.mccfr import MCCFRAgent
from app.ai.strategy import RandomStrategy, RuleBasedStrategy, MCTSStrategy
from app.ai.state import GameStateInfo, ActionSpace
from app.game.deck import Card

@pytest.fixture
def game_state():
    return GameStateInfo(
        available_cards=[
            Card(rank, suit)
            for rank in ['A', 'K', 'Q']
            for suit in ['♥', '♦', '♣', '♠']
        ],
        hand_cards=[
            Card('A', '♥'),
            Card('K', '♦'),
            Card('Q', '♣')
        ],
        top_line=[],
        middle_line=[],
        bottom_line=[],
        opponent_visible={},
        street=1,
        is_fantasy=False
    )

@pytest.fixture
def mccfr_agent():
    return MCCFRAgent(player_id="test_player")

@pytest.fixture
def action_space():
    return ActionSpace()

def test_mccfr_initialization(mccfr_agent):
    assert mccfr_agent.policy_network is not None
    assert mccfr_agent.regret_sum == {}
    assert mccfr_agent.strategy_sum == {}
    assert mccfr_agent.iterations == 0

def test_action_space(action_space, game_state):
    valid_actions = action_space.get_valid_actions(game_state)
    assert len(valid_actions) > 0
    assert all(action['type'] == 'place_card' for action in valid_actions)

def test_state_conversion(game_state):
    state_vector = game_state.to_numpy()
    assert isinstance(state_vector, np.ndarray)
    assert state_vector.shape == (220,)

def test_mccfr_get_action(mccfr_agent, game_state):
    action = mccfr_agent.get_action(game_state)
    assert isinstance(action, dict)
    assert 'type' in action
    assert 'card' in action
    assert 'position' in action
    assert 'index' in action

def test_random_strategy():
    strategy = RandomStrategy()
    game_state = GameStateInfo(
        available_cards=[Card('A', '♥')],
        hand_cards=[Card('A', '♥')],
        top_line=[],
        middle_line=[],
        bottom_line=[],
        opponent_visible={},
        street=1,
        is_fantasy=False
    )
    action = strategy.get_action(game_state)
    assert isinstance(action, dict)

def test_rule_based_strategy():
    strategy = RuleBasedStrategy()
    game_state = GameStateInfo(
        available_cards=[
            Card('A', '♥'),
            Card('A', '♦')
        ],
        hand_cards=[
            Card('A', '♥'),
            Card('A', '♦')
        ],
        top_line=[],
        middle_line=[],
        bottom_line=[],
        opponent_visible={},
        street=1,
        is_fantasy=False
    )
    action = strategy.get_action(game_state)
    assert isinstance(action, dict)
    # Проверяем, что стратегия предпочитает размещать пару в верхней линии
    assert action['position'] == 'top'

def test_mcts_strategy():
    strategy = MCTSStrategy(simulation_count=10)
    game_state = GameStateInfo(
        available_cards=[Card('A', '♥')],
        hand_cards=[Card('A', '♥')],
        top_line=[],
        middle_line=[],
        bottom_line=[],
        opponent_visible={},
        street=1,
        is_fantasy=False
    )
    action = strategy.get_action(game_state)
    assert isinstance(action, dict)

def test_model_save_load(mccfr_agent, tmp_path):
    # Сохраняем модель
    save_path = tmp_path / "model.pt"
    mccfr_agent.save_model(str(save_path))
    
    # Создаем новый агент и загружаем модель
    new_agent = MCCFRAgent(player_id="test_player")
    new_agent.load_model(str(save_path))
    
    # Проверяем, что состояния совпадают
    assert new_agent.iterations == mccfr_agent.iterations
    assert len(new_agent.regret_sum) == len(mccfr_agent.regret_sum)

def test_progress_serialization(mccfr_agent):
    # Проверяем сохранение прогресса
    state = {
        'iterations': 100,
        'regret_sum': {'test': 1.0},
        'strategy_sum': {'test': 1.0}
    }
    success = mccfr_agent.save_state()
    assert success

    # Загружаем прогресс
    loaded_state = mccfr_agent.load_state()
    assert loaded_state is not None
