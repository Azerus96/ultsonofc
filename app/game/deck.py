from typing import List, Dict
import random

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def to_dict(self) -> Dict:
        return {
            'rank': self.rank,
            'suit': self.suit
        }

class Deck:
    SUITS = ['♥', '♦', '♣', '♠']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self) -> None:
        self.cards = [Card(rank, suit) for suit in self.SUITS for rank in self.RANKS]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self, count: int = 1) -> List[Card]:
        if len(self.cards) < count:
            self.reset()
        drawn = self.cards[:count]
        self.cards = self.cards[count:]
        return drawn

    def draw_specific(self, cards_to_draw: List[Dict]) -> List[Card]:
        """Вытягивает конкретные карты (для тестирования и ИИ)"""
        result = []
        for card_dict in cards_to_draw:
            card = next(
                (c for c in self.cards 
                 if c.rank == card_dict['rank'] and c.suit == card_dict['suit']),
                None
            )
            if card:
                self.cards.remove(card)
                result.append(card)
        return result
