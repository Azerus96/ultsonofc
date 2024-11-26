from typing import List, Dict, Tuple
from .deck import Card
from collections import Counter

class HandEvaluator:
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    @classmethod
    def evaluate_line(cls, cards: List[Card]) -> Tuple[int, str]:
        if not cards:
            return (0, "")
        
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]
        rank_counts = Counter(ranks)
        
        # Проверка на роял-флеш
        if (len(cards) == 5 and len(set(suits)) == 1 and 
            set(ranks) == {'10', 'J', 'Q', 'K', 'A'}):
            return (9, "Royal Flush")
            
        # Проверка на стрит-флеш
        if len(cards) == 5:
            is_flush = len(set(suits)) == 1
            values = sorted([cls.RANK_VALUES[r] for r in ranks])
            is_straight = values == list(range(min(values), max(values) + 1))
            if is_flush and is_straight:
                return (8, "Straight Flush")

        # Каре
        if 4 in rank_counts.values():
            return (7, "Four of a Kind")

        # Фулл-хаус
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            return (6, "Full House")

        # Флеш
        if len(cards) == 5 and len(set(suits)) == 1:
            return (5, "Flush")

        # Стрит
        if len(cards) == 5:
            values = sorted([cls.RANK_VALUES[r] for r in ranks])
            if values == list(range(min(values), max(values) + 1)):
                return (4, "Straight")

        # Тройка
        if 3 in rank_counts.values():
            return (3, "Three of a Kind")

        # Две пары
        if list(rank_counts.values()).count(2) == 2:
            return (2, "Two Pair")

        # Пара
        if 2 in rank_counts.values():
            return (1, "Pair")

        # Старшая карта
        return (0, "High Card")

    @classmethod
    def calculate_royalties(cls, position: str, cards: List[Card]) -> int:
        score, combination = cls.evaluate_line(cards)
        
        if position == 'top':
            # Бонусы для верхней линии
            if len(cards) == 3:
                ranks = [card.rank for card in cards]
                if len(set(ranks)) == 1:  # Сет
                    rank_value = cls.RANK_VALUES[ranks[0]]
                    return rank_value + 8  # Бонус за сет
                elif len(set(ranks)) == 2:  # Пара
                    rank = max(ranks, key=ranks.count)
                    if rank == 'Q': return 1
                    elif rank == 'K': return 2
                    elif rank == 'A': return 3
            return 0
            
        elif position == 'middle':
            # Бонусы для средней линии
            bonuses = {
                "Three of a Kind": 2,
                "Straight": 4,
                "Flush": 8,
                "Full House": 12,
                "Four of a Kind": 20,
                "Straight Flush": 30,
                "Royal Flush": 50
            }
            return bonuses.get(combination, 0)
            
        else:  # bottom
            # Бонусы для нижней линии
            bonuses = {
                "Straight": 2,
                "Flush": 4,
                "Full House": 6,
                "Four of a Kind": 10,
                "Straight Flush": 15,
                "Royal Flush": 25
            }
            return bonuses.get(combination, 0)

    @classmethod
    def is_valid_hand(cls, hand: Dict[str, List[Card]]) -> bool:
        """Проверяет, что рука валидна (нет нарушения правила линий)"""
        if not all(len(hand[pos]) == length for pos, length in 
                  [('top', 3), ('middle', 5), ('bottom', 5)]):
            return False

        top_score = cls.evaluate_line(hand['top'])[0]
        middle_score = cls.evaluate_line(hand['middle'])[0]
        bottom_score = cls.evaluate_line(hand['bottom'])[0]

        return top_score <= middle_score <= bottom_score
