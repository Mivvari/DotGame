from collections import deque
import random

import pytest

from app import app
from bot import choose_move
from core import candidate_moves, find_captured, is_free
from simulate import simulate

DIAMOND = {(0, 1), (1, 0), (2, 1), (1, 2)}


def test_diagonal_ring_and_gap():
    assert find_captured(DIAMOND, {(1, 1), (3, 3)}) == {(1, 1)}
    assert find_captured(DIAMOND - {(0, 1)}, {(1, 1)}) == set()


def test_nested_rings_and_multiple_targets():
    square = {(x, y) for x in range(7) for y in range(7)
              if x in (0, 6) or y in (0, 6)}
    inner = {(x + 2, y + 2) for x, y in DIAMOND}
    targets = {(1, 1), (3, 3), (5, 5), (8, 8)}
    assert find_captured(square | inner, targets) == targets - {(8, 8)}


def test_far_apart_rings_and_negative_coordinates():
    shift = 10**12
    rings = DIAMOND | {(x - shift, y - shift) for x, y in DIAMOND}
    targets = {(1, 1), (1 - shift, 1 - shift), (shift, shift)}
    assert find_captured(rings, targets) == targets - {(shift, shift)}


def test_board_edge_is_not_a_wall():
    assert not find_captured({(0, 1), (1, 1), (1, 0)}, {(0, 0)})


def test_moves_and_positions():
    assert is_free(-100, 20, set(), set(), None)
    assert not is_free(-1, 0, set(), set(), 100)
    assert not is_free(100, 0, set(), set(), 100)
    assert not is_free(True, 0, set(), set())
    assert not is_free(1, 1, {(1, 1)}, set())
    assert is_free(1, 1, set(), DIAMOND, 100)  # Внутри кольца ходить можно.
    assert candidate_moves(set(), set(), 100) == {(50, 50)}
    assert candidate_moves(set(), set(), None) == {(0, 0)}
    assert candidate_moves({(0, 0)}, set(), 2) == {(1, 0), (0, 1), (1, 1)}
    assert (2, 2) in candidate_moves({(0, 0)}, set(), None, radius=2)


def test_capture_matches_reference_flood():
    # Сравниваем оптимизацию с буквальным алгоритмом из задания.
    rng = random.Random(71)
    grid = {(x, y) for x in range(8) for y in range(8)}
    for _ in range(120):
        walls = {p for p in sorted(grid) if rng.random() < .48}
        targets = grid - walls
        wet = {(-1, -1)}
        queue = deque(wet)
        while queue:
            x, y = queue.popleft()
            for p in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if -1 <= p[0] <= 8 and -1 <= p[1] <= 8 and p not in walls | wet:
                    wet.add(p)
                    queue.append(p)
        assert find_captured(walls, targets) == targets - wet


def test_bot_wins_blocks_and_does_not_mutate():
    mine = DIAMOND - {(1, 0)}
    enemy = {(1, 1)}
    before = mine.copy(), enemy.copy()
    assert choose_move(mine, enemy, 10, 2) == (1, 0)
    assert (mine, enemy) == before
    assert choose_move(enemy, mine, 10, 2) == (1, 0)


def test_bot_full_board_and_zero_budget():
    assert choose_move({(0, 0)}, set(), 1) is None
    assert choose_move(set(), set(), None, 0) == (0, 0)
    assert is_free(*choose_move({(-5, -5)}, {(0, 0)}, None, 0), {(-5, -5)}, {(0, 0)}, None)


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_api_examples(client):
    response = client.post('/api/move', json={'size': 100, 'me': [[50, 50], [51, 50]], 'enemy': [[50, 51]]})
    assert response.status_code == 200
    assert is_free(**response.json, mine={(50, 50), (51, 50)}, enemy={(50, 51)}, size=100)
    response = client.post('/api/score', json={'size': 100, 'blue': [[1, 1]], 'red': [[2, 2]]})
    assert response.json == {'blue_captured': [], 'red_captured': []}
    response = client.post('/api/score', json={'size': 100, 'blue': [[1, 1]], 'red': list(map(list, DIAMOND))})
    assert response.json == {'blue_captured': [[1, 1]], 'red_captured': []}


@pytest.mark.parametrize('payload', [
    [], {}, {'size': False, 'me': [], 'enemy': []},
    {'size': 0, 'me': [], 'enemy': []},
    {'me': [[1.5, 2]], 'enemy': []},
    {'me': [[True, 2]], 'enemy': []},
    {'me': [[100, 2]], 'enemy': []},
    {'me': [[-1, 2]], 'enemy': []},
    {'me': [[1, 2], [1, 2]], 'enemy': []},
    {'me': [[1, 2]], 'enemy': [[1, 2]]},
    {'me': [[1, 2, 3]], 'enemy': []},
    {'me': [], 'enemy': [], 'time_limit': -1},
    {'me': [], 'enemy': [], 'time_limit': True},
    {'me': [], 'enemy': [], 'time_limit': 10},
])
def test_invalid_json_fields(client, payload):
    response = client.post('/api/move', json=payload)
    assert response.status_code == 400
    assert 'error' in response.json


def test_api_full_unbounded_and_bad_json(client):
    response = client.post('/api/move', json={'size': 1, 'me': [[0, 0]], 'enemy': []})
    assert response.status_code == 409 and response.json['code'] == 'board_full'
    response = client.post('/api/move', json={'size': None, 'me': [[-2, -2]], 'enemy': [], 'time_limit': 0})
    assert response.status_code == 200
    response = client.post('/api/score', json={'size': 200, 'blue': [[199, 199]], 'red': []})
    assert response.status_code == 200
    assert client.post('/api/move', data='{', content_type='application/json').status_code == 400
    assert client.post('/api/move', data='plain text').status_code == 400
    assert client.post('/api/move', data='x' * (1024 * 1024 + 1), content_type='application/json').status_code == 413


def test_web_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert '<canvas' in response.text


def test_simulation():
    result = simulate(size=6, moves=36, time_limit=.01)
    assert result['moves'] == 36
    assert 0 <= result['blue_score'] <= 18
    assert 0 <= result['red_score'] <= 18
