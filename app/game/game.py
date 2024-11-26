from typing import Dict, List, Optional
from .deck import Deck, Card
from .player import Player, PlayerManager
from .hand import Hand
from ..utils.scorer import ScoreCalculator
from ..ai.mccfr import MCCFRAgent
import asyncio
import logging

logger = logging.getLogger(__name__)

class GameState:
    WAITING = "waiting"
    DEALING = "dealing"
    PLAYING = "playing"
    FANTASY = "fantasy"
    SCORING = "scoring"
    FINISHED = "finished"

class Game:
    def __init__(self):
        self.deck = Deck()
        self.player_manager = PlayerManager()
        self.state = GameState.WAITING
        self.current_street = 0
        self.ai_agent = MCCFRAgent(player_id="ai_player")
        self.current_player_id: Optional[str] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.fantasy_players: List[str] = []

    async def start_game(self) -> None:
        """Начало новой игры"""
        if len(self.player_manager.players) < 2:
            raise ValueError("Недостаточно игроков для начала игры")

        self.deck.reset()
        self.player_manager.reset_all()
        self.state = GameState.DEALING
        self.current_street = 1
        
        # Раздача начальных карт
        for player in self.player_manager.players.values():
            initial_cards = self.deck.draw(5)
            player.add_cards(initial_cards)

        self.current_player_id = next(iter(self.player_manager.players))
        await self.start_turn_timer()

    async def start_turn_timer(self) -> None:
        """Запуск таймера хода"""
        if self.timer_task:
            self.timer_task.cancel()

        player = self.player_manager.get_player(self.current_player_id)
        if player:
            self.timer_task = asyncio.create_task(self.handle_turn_timeout(player))

    async def handle_turn_timeout(self, player: Player) -> None:
        """Обработка таймаута хода"""
        try:
            await asyncio.sleep(player.time_bank)
            await self.auto_complete_turn(player)
        except asyncio.CancelledError:
            pass

    async def auto_complete_turn(self, player: Player) -> None:
        """Автоматическое завершение хода при таймауте"""
        if player.is_ai:
            await self.handle_ai_turn(player)
        else:
            # Автоматическая расстановка карт
            current_cards = player.hand.current_cards
            for card in current_cards[:]:
                if len(player.hand.bottom) < 5:
                    player.hand.place_card(card, 'bottom', len(player.hand.bottom))
                elif len(player.hand.middle) < 5:
                    player.hand.place_card(card, 'middle', len(player.hand.middle))
                elif len(player.hand.top) < 3:
                    player.hand.place_card(card, 'top', len(player.hand.top))

        await self.next_turn()

    async def handle_ai_turn(self, player: Player) -> None:
        """Обработка хода ИИ"""
        if not player.is_ai:
            return

        # Получаем решение от ИИ
        game_state = self.get_game_state_for_ai()
        action = self.ai_agent.get_action(game_state)
        
        # Применяем решение ИИ
        await self.apply_ai_action(player, action)

    async def apply_ai_action(self, player: Player, action: Dict) -> None:
        """Применение действия ИИ"""
        # Реализация применения действия ИИ
        pass

    def get_game_state_for_ai(self) -> Dict:
        """Получение состояния игры для ИИ"""
        return {
            'current_street': self.current_street,
            'players': {
                player_id: player.to_dict()
                for player_id, player in self.player_manager.players.items()
            },
            'state': self.state,
            'fantasy_players': self.fantasy_players
        }

    async def next_turn(self) -> None:
        """Переход к следующему ходу"""
        if self.timer_task:
            self.timer_task.cancel()

        # Определяем следующего игрока
        player_ids = list(self.player_manager.players.keys())
        current_index = player_ids.index(self.current_player_id)
        next_index = (current_index + 1) % len(player_ids)
        self.current_player_id = player_ids[next_index]

        # Проверяем, нужно ли переходить к следующей улице
        all_players_completed = all(
            self.is_street_completed(player) 
            for player in self.player_manager.players.values()
        )

        if all_players_completed:
            await self.next_street()
        else:
            await self.start_turn_timer()

    def is_street_completed(self, player: Player) -> bool:
        """Проверка завершения текущей улицы игроком"""
        if self.current_street == 1:
            return len(player.hand.current_cards) == 0
        else:
            return len(player.hand.current_cards) == 1  # Одна карта должна быть сброшена

    async def next_street(self) -> None:
        """Переход к следующей улице"""
        self.current_street += 1
        
        if self.current_street > 5:
            await self.check_fantasy()
        else:
            # Раздача карт для следующей улицы
            for player in self.player_manager.players.values():
                if not player.is_ready:
                    continue
                new_cards = self.deck.draw(3)
                player.add_cards(new_cards)

            self.current_player_id = next(iter(self.player_manager.players))
            await self.start_turn_timer()

    async def check_fantasy(self) -> None:
        """Проверка на возможность фантазии"""
        self.fantasy_players = []
        
        for player_id, player in self.player_manager.players.items():
            if ScoreCalculator.is_fantasy_qualified(player.hand):
                self.fantasy_players.append(player_id)

        if self.fantasy_players:
            self.state = GameState.FANTASY
            await self.start_fantasy()
        else:
            await self.end_game()

    async def start_fantasy(self) -> None:
        """Начало фазы фантазии"""
        # Раздача карт для фантазии
        for player_id in self.fantasy_players:
            player = self.player_manager.get_player(player_id)
            if player:
                player.reset()
                fantasy_cards = self.deck.draw(14)
                player.add_cards(fantasy_cards)
                player.fantasy_count += 1

        # Остальные игроки получают обычную раздачу
        non_fantasy_players = set(self.player_manager.players.keys()) - set(self.fantasy_players)
        for player_id in non_fantasy_players:
            player = self.player_manager.get_player(player_id)
            if player:
                player.reset()
                initial_cards = self.deck.draw(5)
                player.add_cards(initial_cards)

        self.current_street = 1
        self.current_player_id = next(iter(non_fantasy_players), next(iter(self.fantasy_players)))
        await self.start_turn_timer()

    async def end_game(self) -> None:
        """Завершение игры и подсчет очков"""
        self.state = GameState.SCORING
        
        # Подсчет очков для каждой пары игроков
        player_ids = list(self.player_manager.players.keys())
        for i in range(len(player_ids)):
            for j in range(i + 1, len(player_ids)):
                player1 = self.player_manager.get_player(player_ids[i])
                player2 = self.player_manager.get_player(player_ids[j])
                
                if player1 and player2:
                    score = ScoreCalculator.calculate_hand_score(
                        player1.hand, player2.hand
                    )
                    player1.score += score
                    player2.score -= score

        self.state = GameState.FINISHED

    def get_game_state(self) -> Dict:
        """Получение полного состояния игры"""
        return {
            'state': self.state,
            'current_street': self.current_street,
            'current_player': self.current_player_id,
            'fantasy_players': self.fantasy_players,
            'players': {
                player_id: player.to_dict()
                for player_id, player in self.player_manager.players.items()
            }
        }

    def can_player_move(self, player_id: str) -> bool:
        """Проверка возможности хода игрока"""
        return (
            self.state in [GameState.PLAYING, GameState.FANTASY] and
            self.current_player_id == player_id
        )

    async def handle_player_action(self, player_id: str, action: Dict) -> bool:
        """Обработка действия игрока"""
        if not self.can_player_move(player_id):
            return False

        player = self.player_manager.get_player(player_id)
        if not player:
            return False

        action_type = action.get('type')
        if action_type == 'place_card':
            success = player.place_card(
                action['card'],
                action['position'],
                action['index']
            )
        elif action_type == 'remove_card':
            success = bool(player.remove_card(
                action['position'],
                action['index']
            ))
        else:
            return False

        if success and self.is_street_completed(player):
            await self.next_turn()

        return success
