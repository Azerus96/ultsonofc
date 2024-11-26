from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..game.deck import Card
import numpy as np

@dataclass
class GameStateInfo:
    """Информационное состояние игры для ИИ"""
    available_cards: List[Card]  # Доступные карты
    hand_cards: List[Card]      # Карты в руке
    top_line: List[Card]        # Верхняя линия
    middle_line: List[Card]     # Средняя линия
    bottom_line: List[Card]     # Нижняя линия
    opponent_visible: Dict[str, List[Card]]  # Видимые карты оппонента
    street: int                 # Текущая улица
    is_fantasy: bool           # Режим фантазии

    def to_numpy(self) -> np.ndarray:
        """Преобразование состояния в числовой вектор для ИИ"""
        # Создаем вектор состояния размером 52 * 4 + дополнительные параметры
        state_vector = np.zeros(220)  # 52 карты * 4 позиции + 12 доп. параметров
        
        # Кодируем карты (0-51) для каждой позиции
        def encode_cards(cards: List[Card], offset: int):
            for card in cards:
                idx = self._card_to_index(card)
                state_vector[offset + idx] = 1

        # Кодируем карты в разных позициях
        encode_cards(self.hand_cards, 0)        # 0-51
        encode_cards(self.top_line, 52)         # 52-103
        encode_cards(self.middle_line, 104)     # 104-155
        encode_cards(self.bottom_line, 156)     # 156-207

        # Дополнительные параметры
        state_vector[208] = self.street / 5     # Нормализованный номер улицы
        state_vector[209] = int(self.is_fantasy)
        
        # Кодируем видимые карты оппонента
        visible_cards = [card for cards in self.opponent_visible.values() for card in cards]
        encode_cards(visible_cards, 210)

        return state_vector

    @staticmethod
    def _card_to_index(card: Card) -> int:
        """Преобразование карты в индекс (0-51)"""
        suits = {'♥': 0, '♦': 1, '♣': 2, '♠': 3}
        ranks = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
                '9': 7, '10': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
        return ranks[card.rank] * 4 + suits[card.suit]

class ActionSpace:
    """Пространство действий для ИИ"""
    def __init__(self):
        self.positions = ['top', 'middle', 'bottom']
        self.max_indices = {'top': 3, 'middle': 5, 'bottom': 5}

    def get_valid_actions(self, state: GameStateInfo) -> List[Dict]:
        """Получение списка возможных действий"""
        valid_actions = []
        
        # Для каждой карты в руке
        for card in state.hand_cards:
            # Для каждой возможной позиции
            for position in self.positions:
                current_line = getattr(state, f"{position}_line")
                max_cards = self.max_indices[position]
                
                # Если в линии есть место
                if len(current_line) < max_cards:
                    # Добавляем все возможные индексы для размещения
                    for index in range(len(current_line) + 1):
                        valid_actions.append({
                            'type': 'place_card',
                            'card': card,
                            'position': position,
                            'index': index
                        })

        return valid_actions

    def action_to_vector(self, action: Dict) -> np.ndarray:
        """Преобразование действия в вектор"""
        # Размер вектора: 52 карты * 13 позиций (3+5+5 индексов)
        vector_size = 52 * 13
        vector = np.zeros(vector_size)
        
        if action['type'] == 'place_card':
            card_idx = GameStateInfo._card_to_index(action['card'])
            position_offset = {
                'top': 0,
                'middle': 3,
                'bottom': 8
            }[action['position']]
            
            idx = card_idx * 13 + position_offset + action['index']
            vector[idx] = 1
            
        return vector

    def vector_to_action(self, vector: np.ndarray) -> Dict:
        """Преобразование вектора в действие"""
        idx = np.argmax(vector)
        card_idx = idx // 13
        position_idx = idx % 13
        
        # Определяем позицию и индекс
        if position_idx < 3:
            position = 'top'
            index = position_idx
        elif position_idx < 8:
            position = 'middle'
            index = position_idx - 3
        else:
            position = 'bottom'
            index = position_idx - 8
            
        # Восстанавливаем карту из индекса
        suit_idx = card_idx % 4
        rank_idx = card_idx // 4
        
        suits = ['♥', '♦', '♣', '♠']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        return {
            'type': 'place_card',
            'card': Card(ranks[rank_idx], suits[suit_idx]),
            'position': position,
            'index': index
        }
