import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple
import os
from .state import GameStateInfo, ActionSpace
from ..utils.serializer import ProgressSerializer

class PolicyNetwork(nn.Module):
    def __init__(self, input_size: int = 220, hidden_size: int = 512):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, 52 * 13)  # Все возможные действия
        
        self.dropout = nn.Dropout(0.3)
        self.batch_norm1 = nn.BatchNorm1d(hidden_size)
        self.batch_norm2 = nn.BatchNorm1d(hidden_size)
        self.batch_norm3 = nn.BatchNorm1d(hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.batch_norm1(self.fc1(x)))
        x = self.dropout(x)
        x = F.relu(self.batch_norm2(self.fc2(x)))
        x = self.dropout(x)
        x = F.relu(self.batch_norm3(self.fc3(x)))
        x = self.dropout(x)
        return F.softmax(self.fc4(x), dim=-1)

class MCCFRAgent:
    def __init__(self, player_id: str, learning_rate: float = 0.001, 
                 exploration_factor: float = 0.4):
        self.player_id = player_id
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_network = PolicyNetwork().to(self.device)
        self.optimizer = torch.optim.Adam(
            self.policy_network.parameters(), 
            lr=learning_rate
        )
        self.action_space = ActionSpace()
        self.regret_sum = {}
        self.strategy_sum = {}
        self.iterations = 0
        self.exploration_factor = exploration_factor
        
        # Инициализация сериализатора с токеном из окружения
        self.serializer = ProgressSerializer(
            token=os.environ.get('AI_PROGRESS_TOKEN'),
            player_id=player_id
        )
        
        # Загрузка сохраненного состояния
        self.load_saved_state()

    def get_strategy(self, state: GameStateInfo) -> np.ndarray:
        """Получение стратегии для текущего состояния"""
        state_key = self._state_to_key(state)
        valid_actions = self.action_space.get_valid_actions(state)
        
        if not valid_actions:
            return np.array([])

        # Получаем регреты для всех действий
        regrets = np.array([
            max(0, self.regret_sum.get(f"{state_key}_{i}", 0))
            for i in range(len(valid_actions))
        ])

        # Нормализуем регреты в стратегию
        regret_sum = np.sum(regrets)
        if regret_sum > 0:
            strategy = regrets / regret_sum
        else:
            strategy = np.ones(len(valid_actions)) / len(valid_actions)

        # Добавляем исследование
        if self.iterations < 1000:  # Больше исследования на ранних итерациях
            strategy = (1 - self.exploration_factor) * strategy + \
                      self.exploration_factor * np.random.dirichlet(
                          np.ones(len(valid_actions))
                      )

        return strategy

    def update_regrets(self, state: GameStateInfo, action_index: int, 
                      utility: float, node_utility: float) -> None:
        """Обновление сумм регретов"""
        state_key = self._state_to_key(state)
        counterfactual_regret = utility - node_utility
        
        self.regret_sum[f"{state_key}_{action_index}"] = \
            self.regret_sum.get(f"{state_key}_{action_index}", 0) + \
            counterfactual_regret

    def train(self, state: GameStateInfo) -> float:
        """Одна итерация обучения"""
        if self._is_terminal(state):
            return self._get_utility(state)

        valid_actions = self.action_space.get_valid_actions(state)
        if not valid_actions:
            return 0.0

        # Получаем стратегию
        strategy = self.get_strategy(state)
        
        # Обновляем сумму стратегий для усреднения
        state_key = self._state_to_key(state)
        for i, action_prob in enumerate(strategy):
            self.strategy_sum[f"{state_key}_{i}"] = \
                self.strategy_sum.get(f"{state_key}_{i}", 0) + action_prob

        # Выбираем действие и рекурсивно вычисляем полезность
        action_utilities = np.zeros(len(valid_actions))
        
        for i, action in enumerate(valid_actions):
            next_state = self._apply_action(state.copy(), action)
            action_utilities[i] = -self.train(next_state)  # Рекурсивный вызов

        # Вычисляем общую полезность узла
        node_utility = np.sum(strategy * action_utilities)

        # Обновляем регреты
        for i, utility in enumerate(action_utilities):
            self.update_regrets(state, i, utility, node_utility)

        self.iterations += 1
        
        # Периодически сохраняем прогресс
        if self.iterations % 1000 == 0:
            self.save_state()

        return node_utility

    def get_action(self, state: GameStateInfo) -> Dict:
        """Получение действия на основе текущей стратегии"""
        valid_actions = self.action_space.get_valid_actions(state)
        if not valid_actions:
            return {}

        # Используем нейронную сеть для получения вероятностей действий
        state_tensor = torch.FloatTensor(state.to_numpy()).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs = self.policy_network(state_tensor).cpu().numpy()[0]

        # Фильтруем и нормализуем вероятности только для допустимых действий
        valid_probs = []
        for action in valid_actions:
            action_vector = self.action_space.action_to_vector(action)
            prob = np.sum(action_probs * action_vector)
            valid_probs.append(prob)

        valid_probs = np.array(valid_probs)
        valid_probs = valid_probs / np.sum(valid_probs)

        # Выбираем действие
        if np.random.random() < self.exploration_factor:
            action_idx = np.random.choice(len(valid_actions))
        else:
            action_idx = np.argmax(valid_probs)
            
        return valid_actions[action_idx]

    def update_policy_network(self, state: GameStateInfo, reward: float) -> None:
        """Обновление нейронной сети на основе полученного вознаграждения"""
        state_tensor = torch.FloatTensor(state.to_numpy()).unsqueeze(0).to(self.device)
        reward_tensor = torch.FloatTensor([reward]).to(self.device)

        self.optimizer.zero_grad()
        action_probs = self.policy_network(state_tensor)
        
        # Используем функцию потерь policy gradient
        loss = -torch.log(action_probs.mean()) * reward_tensor
        loss = loss.mean()
        
        loss.backward()
        self.optimizer.step()

    def save_state(self) -> bool:
        """Сохранение состояния агента"""
        try:
            state = {
                'policy_network': self.policy_network.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'regret_sum': self.regret_sum,
                'strategy_sum': self.strategy_sum,
                'iterations': self.iterations,
                'exploration_factor': self.exploration_factor
            }
            return self.serializer.save_progress(state)
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_saved_state(self) -> None:
        """Загрузка сохраненного состояния"""
        try:
            state = self.serializer.load_progress()
            if state:
                self.policy_network.load_state_dict(state['policy_network'])
                self.optimizer.load_state_dict(state['optimizer'])
                self.regret_sum = state['regret_sum']
                self.strategy_sum = state['strategy_sum']
                self.iterations = state['iterations']
                self.exploration_factor = state['exploration_factor']
        except Exception as e:
            print(f"Error loading state: {e}")

    @staticmethod
    def _state_to_key(state: GameStateInfo) -> str:
        """Преобразование состояния в строковый ключ"""
        return f"{state.street}_{len(state.hand_cards)}_{len(state.top_line)}_" \
               f"{len(state.middle_line)}_{len(state.bottom_line)}"

    @staticmethod
    def _is_terminal(state: GameStateInfo) -> bool:
        """Проверка, является ли состояние терминальным"""
        return (len(state.hand_cards) == 0 and 
                len(state.top_line) == 3 and 
                len(state.middle_line) == 5 and 
                len(state.bottom_line) == 5)

    def _get_utility(self, state: GameStateInfo) -> float:
        """Получение полезности терминального состояния"""
        from ..game.evaluator import HandEvaluator
        
        # Оцениваем каждую линию
        top_score = HandEvaluator.evaluate_line(state.top_line)[0]
        middle_score = HandEvaluator.evaluate_line(state.middle_line)[0]
        bottom_score = HandEvaluator.evaluate_line(state.bottom_line)[0]
        
        # Проверяем валидность руки
        if not (top_score <= middle_score <= bottom_score):
            return -1.0  # Штраф за невалидную руку
        
        # Считаем бонусы
        royalties = (
            HandEvaluator.calculate_royalties('top', state.top_line) +
            HandEvaluator.calculate_royalties('middle', state.middle_line) +
            HandEvaluator.calculate_royalties('bottom', state.bottom_line)
        )
        
        # Возвращаем общую оценку
        return float(top_score + middle_score + bottom_score + royalties)

    @staticmethod
    def _apply_action(state: GameStateInfo, action: Dict) -> GameStateInfo:
        """Применение действия к состоянию"""
        new_state = GameStateInfo(
            available_cards=state.available_cards.copy(),
            hand_cards=state.hand_cards.copy(),
            top_line=state.top_line.copy(),
            middle_line=state.middle_line.copy(),
            bottom_line=state.bottom_line.copy(),
            opponent_visible=state.opponent_visible.copy(),
            street=state.street,
            is_fantasy=state.is_fantasy
        )

        if action['type'] == 'place_card':
            card = action['card']
            position = action['position']
            index = action['index']
            
            # Удаляем карту из руки
            new_state.hand_cards.remove(card)
            
            # Добавляем карту в соответствующую линию
            target_line = getattr(new_state, f"{position}_line")
            target_line.insert(index, card)

        return new_state

    def reset(self) -> None:
        """Сброс состояния агента"""
        self.regret_sum = {}
        self.strategy_sum = {}
        self.iterations = 0
        self.exploration_factor = 0.4
        
        # Реинициализация нейронной сети
        self.policy_network = PolicyNetwork().to(self.device)
        self.optimizer = torch.optim.Adam(
            self.policy_network.parameters(), 
            lr=0.001
        )
