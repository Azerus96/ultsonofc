from typing import Dict, Optional, List
from .hand import Hand
from .deck import Card

class Player:
    def __init__(self, player_id: str, name: str, is_ai: bool = False):
        self.id = player_id
        self.name = name
        self.hand = Hand()
        self.is_ai = is_ai
        self.score = 0
        self.fantasy_count = 0
        self.time_bank = 60  # секунды
        self.is_ready = False

    def reset(self) -> None:
        """Сброс состояния игрока для новой игры"""
        self.hand = Hand()
        self.fantasy_count = 0
        self.is_ready = False

    def add_cards(self, cards: List[Card]) -> None:
        """Добавление карт в руку игрока"""
        self.hand.add_cards(cards)

    def place_card(self, card_dict: Dict, position: str, index: int) -> bool:
        """Размещение карты в определенную позицию"""
        card = next(
            (c for c in self.hand.current_cards 
             if c.rank == card_dict['rank'] and c.suit == card_dict['suit']),
            None
        )
        if card:
            return self.hand.place_card(card, position, index)
        return False

    def remove_card(self, position: str, index: int) -> Optional[Card]:
        """Удаление карты с определенной позиции"""
        return self.hand.remove_card(position, index)

    def to_dict(self) -> Dict:
        """Преобразование состояния игрока в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'hand': self.hand.to_dict(),
            'score': self.score,
            'fantasy_count': self.fantasy_count,
            'time_bank': self.time_bank,
            'is_ready': self.is_ready,
            'is_ai': self.is_ai
        }

class PlayerManager:
    def __init__(self):
        self.players: Dict[str, Player] = {}

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            del self.players[player_id]

    def get_player(self, player_id: str) -> Optional[Player]:
        return self.players.get(player_id)

    def reset_all(self) -> None:
        for player in self.players.values():
            player.reset()
