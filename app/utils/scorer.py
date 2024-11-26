from typing import Dict, List
from ..game.evaluator import HandEvaluator
from ..game.hand import Hand

class ScoreCalculator:
    @staticmethod
    def calculate_hand_score(player_hand: Hand, opponent_hand: Hand) -> int:
        """Подсчитывает очки за одну руку между двумя игроками"""
        score = 0
        
        # Сравниваем каждую линию
        positions = [('top', 1), ('middle', 1), ('bottom', 1)]
        for position, points in positions:
            player_cards = getattr(player_hand, position)
            opponent_cards = getattr(opponent_hand, position)
            
            player_score = HandEvaluator.evaluate_line(player_cards)[0]
            opponent_score = HandEvaluator.evaluate_line(opponent_cards)[0]
            
            if player_score > opponent_score:
                score += points
            elif player_score < opponent_score:
                score -= points

        # Бонус за выигрыш всех линий
        if score == 3:
            score += 3
        elif score == -3:
            score -= 3

        # Добавляем royalties
        player_royalties = sum(
            HandEvaluator.calculate_royalties(pos, getattr(player_hand, pos))
            for pos, _ in positions
        )
        opponent_royalties = sum(
            HandEvaluator.calculate_royalties(pos, getattr(opponent_hand, pos))
            for pos, _ in positions
        )
        
        score += player_royalties - opponent_royalties
        
        return score

    @staticmethod
    def is_fantasy_qualified(hand: Hand) -> bool:
        """Проверяет, квалифицируется ли рука для фантазии"""
        if not hand.is_complete():
            return False
            
        # Проверяем верхнюю линию на наличие QQ или выше
        top_cards = hand.top
        if len(top_cards) != 3:
            return False
            
        ranks = [card.rank for card in top_cards]
        rank_counts = Counter(ranks)
        
        if len(rank_counts) != 2:  # Должна быть пара
            return False
            
        pair_rank = max(ranks, key=ranks.count)
        return (HandEvaluator.RANK_VALUES[pair_rank] >= 
                HandEvaluator.RANK_VALUES['Q'])
