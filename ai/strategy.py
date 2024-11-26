from typing import Dict, List, Optional
import numpy as np
from .state import GameStateInfo, ActionSpace
from ..game.evaluator import HandEvaluator

class Strategy:
    """Базовый класс для стратегий ИИ"""
    def get_action(self, state: GameStateInfo) -> Dict:
        raise NotImplementedError

class RandomStrategy(Strategy):
    """Случайная стратегия для тестирования"""
    def __init__(self):
        self.action_space = ActionSpace()

    def get_action(self, state: GameStateInfo) -> Dict:
        valid_actions = self.action_space.get_valid_actions(state)
        if not valid_actions:
            return {}
        return np.random.choice(valid_actions)

class RuleBasedStrategy(Strategy):
    """Стратегия на основе правил"""
    def __init__(self):
        self.action_space = ActionSpace()
        self.evaluator = HandEvaluator()

    def get_action(self, state: GameStateInfo) -> Dict:
        valid_actions = self.action_space.get_valid_actions(state)
        if not valid_actions:
            return {}

        # Оцениваем каждое действие
        action_scores = []
        for action in valid_actions:
            score = self._evaluate_action(state, action)
            action_scores.append((score, action))

        # Выбираем действие с наивысшей оценкой
        return max(action_scores, key=lambda x: x[0])[1]

    def _evaluate_action(self, state: GameStateInfo, action: Dict) -> float:
        """Оценка действия на основе правил"""
        position = action['position']
        card = action['card']
        
        # Базовая оценка
        score = 0.0
        
        # Оцениваем карту относительно позиции
        if position == 'top':
            # Для верхней линии предпочитаем пары и тройки
            score += self._evaluate_top_line(state, card)
        elif position == 'middle':
            # Для средней линии предпочитаем стриты и флеши
            score += self._evaluate_middle_line(state, card)
        else:  # bottom
            # Для нижней линии предпочитаем сильные комбинации
            score += self._evaluate_bottom_line(state, card)

        return score

    def _evaluate_top_line(self, state: GameStateInfo, card) -> float:
        current_cards = state.top_line + [card]
        rank_counts = self._count_ranks(current_cards)
        
        # Высокие оценки для пар и троек
        if max(rank_counts.values()) > 1:
            return 10.0 * max(rank_counts.values())
        return float(HandEvaluator.RANK_VALUES[card.rank]) / 14.0

    def _evaluate_middle_line(self, state: GameStateInfo, card) -> float:
        current_cards = state.middle_line + [card]
        score = 0.0
        
        # Проверяем потенциал для стрита
        if self._has_straight_potential(current_cards):
            score += 5.0
            
        # Проверяем потенциал для флеша
        if self._has_flush_potential(current_cards):
            score += 5.0
            
        return score

    def _evaluate_bottom_line(self, state: GameStateInfo, card) -> float:
        current_cards = state.bottom_line + [card]
        score = 0.0
        
        # Предпочитаем высокие карты
        score += HandEvaluator.RANK_VALUES[card.rank] / 14.0
        
        # Проверяем потенциал для сильных комбинаций
        if self._has_straight_potential(current_cards):
            score += 3.0
        if self._has_flush_potential(current_cards):
            score += 3.0
        if self._has_full_house_potential(current_cards):
            score += 5.0
            
        return score

    @staticmethod
    def _count_ranks(cards: List) -> Dict[str, int]:
        return {rank: sum(1 for c in cards if c.rank == rank) 
                for rank in set(c.rank for c in cards)}

    @staticmethod
    def _has_straight_potential(cards: List) -> bool:
        if len(cards) < 3:
            return False
        values = sorted([HandEvaluator.RANK_VALUES[c.rank] for c in cards])
        return max(values) - min(values) <= 4

    @staticmethod
    def _has_flush_potential(cards: List) -> bool:
        if len(cards) < 3:
            return False
        suits = [c.suit for c in cards]
        return max(suits.count(s) for s in set(suits)) >= 3

    @staticmethod
    def _has_full_house_potential(cards: List) -> bool:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        return 3 in rank_counts.values() or list(rank_counts.values()).count(2) >= 2

class MCTSStrategy(Strategy):
    """Стратегия на основе Monte Carlo Tree Search"""
    def __init__(self, simulation_count: int = 100):
        self.action_space = ActionSpace()
        self.simulation_count = simulation_count

    def get_action(self, state: GameStateInfo) -> Dict:
        valid_actions = self.action_space.get_valid_actions(state)
        if not valid_actions:
            return {}

        # Выполняем симуляции для каждого действия
        action_scores = []
        for action in valid_actions:
            score = self._simulate_action(state, action)
            action_scores.append((score, action))

        # Выбираем действие с наилучшим результатом
        return max(action_scores, key=lambda x: x[0])[1]

    def _simulate_action(self, state: GameStateInfo, action: Dict) -> float:
        """Симуляция результата действия"""
        total_score = 0.0
        
        for _ in range(self.simulation_count):
            # Создаем копию состояния
            sim_state = self._copy_state(state)
            
            # Применяем действие
            self._apply_action(sim_state, action)
            
            # Проводим случайную симуляцию до конца игры
            score = self._random_playout(sim_state)
            total_score += score

        return total_score / self.simulation_count

    def _random_playout(self, state: GameStateInfo) -> float:
        """Случайная симуляция до конца игры"""
        while not self._is_terminal(state):
            valid_actions = self.action_space.get_valid_actions(state)
            if not valid_actions:
                break
            action = np.random.choice(valid_actions)
            self._apply_action(state, action)

        return self._evaluate_state(state)

    @staticmethod
    def _copy_state(state: GameStateInfo) -> GameStateInfo:
        """Создание копии состояния"""
        return GameStateInfo(
            available_cards=state.available_cards.copy(),
            hand_cards=state.hand_cards.copy(),
            top_line=state.top_line.copy(),
            middle_line=state.middle_line.copy(),
            bottom_line=state.bottom_line.copy(),
            opponent_visible=state.opponent_visible.copy(),
            street=state.street,
            is_fantasy=state.is_fantasy
        )

    @staticmethod
    def _apply_action(state: GameStateInfo, action: Dict) -> None:
        """Применение действия к состоянию"""
        if action['type'] == 'place_card':
            card = action['card']
            position = action['position']
            target_line = getattr(state, f"{position}_line")
            
            state.hand_cards.remove(card)
            target_line.insert(action['index'], card)

    @staticmethod
    def _is_terminal(state: GameStateInfo) -> bool:
        """Проверка завершения игры"""
        return (len(state.hand_cards) == 0 and 
                len(state.top_line) == 3 and 
                len(state.middle_line) == 5 and 
                len(state.bottom_line) == 5)

    @staticmethod
    def _evaluate_state(state: GameStateInfo) -> float:
        """Оценка конечного состояния"""
        evaluator = HandEvaluator()
        score = 0.0
        
        # Оцениваем каждую линию
        score += evaluator.evaluate_line(state.top_line)[0] * 1.0
        score += evaluator.evaluate_line(state.middle_line)[0] * 1.5
        score += evaluator.evaluate_line(state.bottom_line)[0] * 2.0
        
        return score
