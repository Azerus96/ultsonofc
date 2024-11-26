from typing import List, Dict, Optional
from .deck import Card

class Hand:
    def __init__(self):
        self.top: List[Card] = []      # Верхняя линия (3 карты)
        self.middle: List[Card] = []    # Средняя линия (5 карт)
        self.bottom: List[Card] = []    # Нижняя линия (5 карт)
        self.current_cards: List[Card] = []  # Текущие карты в руке

    def add_cards(self, cards: List[Card]) -> None:
        self.current_cards.extend(cards)

    def place_card(self, card: Card, position: str, index: int) -> bool:
        """Размещает карту в указанную позицию"""
        if card not in self.current_cards:
            return False

        target_line = getattr(self, position)
        max_cards = 3 if position == 'top' else 5

        if len(target_line) >= max_cards:
            return False

        if 0 <= index <= len(target_line):
            target_line.insert(index, card)
            self.current_cards.remove(card)
            return True
        return False

    def remove_card(self, position: str, index: int) -> Optional[Card]:
        """Убирает карту с указанной позиции"""
        target_line = getattr(self, position)
        if 0 <= index < len(target_line):
            card = target_line.pop(index)
            self.current_cards.append(card)
            return card
        return None

    def is_complete(self) -> bool:
        """Проверяет, завершена ли расстановка карт"""
        return (len(self.top) == 3 and 
                len(self.middle) == 5 and 
                len(self.bottom) == 5)

    def to_dict(self) -> Dict:
        return {
            'top': [card.to_dict() for card in self.top],
            'middle': [card.to_dict() for card in self.middle],
            'bottom': [card.to_dict() for card in self.bottom],
            'current': [card.to_dict() for card in self.current_cards]
        }
