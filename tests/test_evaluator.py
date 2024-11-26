import pytest
from app.game.evaluator import HandEvaluator
from app.game.deck import Card

@pytest.fixture
def evaluator():
    return HandEvaluator()

def test_royal_flush():
    cards = [
        Card('10', '♥'),
        Card('J', '♥'),
        Card('Q', '♥'),
        Card('K', '♥'),
        Card('A', '♥')
    ]
    score, name = HandEvaluator.evaluate_line(cards)
    assert name == "Royal Flush"
    assert score == 9

def test_straight_flush():
    cards = [
        Card('9', '♥'),
        Card('10', '♥'),
        Card('J', '♥'),
        Card('Q', '♥'),
        Card('K', '♥')
    ]
    score, name = HandEvaluator.evaluate_line(cards)
    assert name == "Straight Flush"
    assert score == 8

def test_four_of_a_kind():
    cards = [
        Card('A', '♥'),
        Card('A', '♦'),
        Card('A', '♣'),
        Card('A', '♠'),
        Card('K', '♥')
    ]
    score, name = HandEvaluator.evaluate_line(cards)
    assert name == "Four of a Kind"
    assert score == 7

def test_full_house():
    cards = [
        Card('A', '♥'),
        Card('A', '♦'),
        Card('A', '♣'),
        Card('K', '♠'),
        Card('K', '♥')
    ]
    score, name = HandEvaluator.evaluate_line(cards)
    assert name == "Full House"
    assert score == 6

def test_royalties_calculation():
    # Тест для верхней линии
    top_cards = [
        Card('Q', '♥'),
        Card('Q', '♦'),
        Card('K', '♣')
    ]
    royalties = HandEvaluator.calculate_royalties('top', top_cards)
    assert royalties > 0

    # Тест для средней линии
    middle_cards = [
        Card('10', '♥'),
        Card('J', '♥'),
        Card('Q', '♥'),
        Card('K', '♥'),
        Card('A', '♥')
    ]
    royalties = HandEvaluator.calculate_royalties('middle', middle_cards)
    assert royalties == 50  # Royal Flush

    # Тест для нижней линии
    bottom_cards = [
        Card('10', '♥'),
        Card('J', '♥'),
        Card('Q', '♥'),
        Card('K', '♥'),
        Card('A', '♥')
    ]
    royalties = HandEvaluator.calculate_royalties('bottom', bottom_cards)
    assert royalties == 25  # Royal Flush в нижней линии

def test_valid_hand():
    # Тест валидной руки
    hand = {
        'top': [
            Card('J', '♥'),
            Card('J', '♦'),
            Card('Q', '♣')
        ],
        'middle': [
            Card('10', '♥'),
            Card('10', '♦'),
            Card('10', '♣'),
            Card('K', '♠'),
            Card('K', '♥')
        ],
        'bottom': [
            Card('A', '♥'),
            Card('A', '♦'),
            Card('A', '♣'),
            Card('A', '♠'),
            Card('2', '♥')
        ]
    }
    assert HandEvaluator.is_valid_hand(hand)

def test_invalid_hand():
    # Тест невалидной руки (верхняя линия сильнее средней)
    hand = {
        'top': [
            Card('A', '♥'),
            Card('A', '♦'),
            Card('A', '♣')
        ],
        'middle': [
            Card('K', '♥'),
            Card('K', '♦'),
            Card('K', '♣'),
            Card('2', '♠'),
            Card('2', '♥')
        ],
        'bottom': [
            Card('A', '♠'),
            Card('K', '♣'),
            Card('Q', '♣'),
            Card('J', '♣'),
            Card('10', '♣')
        ]
    }
    assert not HandEvaluator.is_valid_hand(hand)

def test_compare_hands():
    hand1 = {
        'top': [
            Card('Q', '♥'),
            Card('Q', '♦'),
            Card('K', '♣')
        ],
        'middle': [
            Card('10', '♥'),
            Card('J', '♥'),
            Card('Q', '♥'),
            Card('K', '♥'),
            Card('A', '♥')
        ],
        'bottom': [
            Card('2', '♣'),
            Card('2', '♦'),
            Card('2', '♥'),
            Card('2', '♠'),
            Card('3', '♣')
        ]
    }

    hand2 = {
        'top': [
            Card('J', '♥'),
            Card('J', '♦'),
            Card('Q', '♣')
        ],
        'middle': [
            Card('10', '♦'),
            Card('J', '♦'),
            Card('Q', '♦'),
            Card('K', '♦'),
            Card('A', '♦')
        ],
        'bottom': [
            Card('3', '♣'),
            Card('3', '♦'),
            Card('3', '♥'),
            Card('3', '♠'),
            Card('4', '♣')
        ]
    }

    # Сравниваем каждую линию
    top_score1, _ = HandEvaluator.evaluate_line(hand1['top'])
    top_score2, _ = HandEvaluator.evaluate_line(hand2['top'])
    assert top_score1 > top_score2

    middle_score1, _ = HandEvaluator.evaluate_line(hand1['middle'])
    middle_score2, _ = HandEvaluator.evaluate_line(hand2['middle'])
    assert middle_score1 == middle_score2  # Оба Royal Flush

    bottom_score1, _ = HandEvaluator.evaluate_line(hand1['bottom'])
    bottom_score2, _ = HandEvaluator.evaluate_line(hand2['bottom'])
    assert bottom_score1 == bottom_score2  # Оба Four of a Kind

def test_fantasy_qualification():
    # Тест на квалификацию фантазии (QQ или выше в верхней линии)
    qualifying_hand = {
        'top': [
            Card('Q', '♥'),
            Card('Q', '♦'),
            Card('K', '♣')
        ],
        'middle': [
            Card('10', '♥'),
            Card('J', '♥'),
            Card('Q', '♥'),
            Card('K', '♥'),
            Card('A', '♥')
        ],
        'bottom': [
            Card('2', '♣'),
            Card('2', '♦'),
            Card('2', '♥'),
            Card('2', '♠'),
            Card('3', '♣')
        ]
    }
    
    non_qualifying_hand = {
        'top': [
            Card('J', '♥'),
            Card('J', '♦'),
            Card('Q', '♣')
        ],
        'middle': [
            Card('10', '♥'),
            Card('J', '♥'),
            Card('Q', '♥'),
            Card('K', '♥'),
            Card('A', '♥')
        ],
        'bottom': [
            Card('2', '♣'),
            Card('2', '♦'),
            Card('2', '♥'),
            Card('2', '♠'),
            Card('3', '♣')
        ]
    }

    assert HandEvaluator.is_valid_hand(qualifying_hand)
    assert HandEvaluator.is_valid_hand(non_qualifying_hand)
    
    # Проверяем квалификацию фантазии
    from app.utils.scorer import ScoreCalculator
    assert ScoreCalculator.is_fantasy_qualified(qualifying_hand)
    assert not ScoreCalculator.is_fantasy_qualified(non_qualifying_hand)
