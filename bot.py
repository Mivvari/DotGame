"""Простой бот: закрывает кольца, мешает сопернику, строит цепочки."""

from math import isfinite
from time import perf_counter

from core import NEIGHBORS, candidate_moves, find_captured


def choose_move(mine, enemy, size=100, time_limit=0.5):
    """Возвращает свободную пару (x, y), либо None на полном поле.

    time_limit — мягкий бюджет: уже начатую проверку захвата завершаем.
    Исходные множества не меняем.
    """
    if not isfinite(time_limit) or time_limit < 0:
        raise ValueError("Время должно быть конечным неотрицательным числом")
    started = perf_counter()
    moves = candidate_moves(mine, enemy, size)
    if not moves:
        return None
    center = (size // 2, size // 2) if size is not None else (0, 0)
    if mine or enemy:
        all_points = mine | enemy
        center = (sum(x for x, _ in all_points) // len(all_points),
                  sum(y for _, y in all_points) // len(all_points))

    def neighbors(point, stones):
        x, y = point
        return sum((x + dx, y + dy) in stones for dx, dy in NEIGHBORS)

    def position_value(point):
        friends = neighbors(point, mine)
        rivals = neighbors(point, enemy)
        # Точки возле двух своих соседей могут замкнуть кольцо.
        distance = abs(point[0] - center[0]) + abs(point[1] - center[1])
        return friends * 3 + rivals * 2 - max(0, friends - 3) * 3 - distance * 0.03

    ranked = sorted(moves, key=lambda p: (-position_value(p), p))
    best = ranked[0]
    best_value = float("-inf")
    if time_limit == 0:
        return best
    already_mine = find_captured(mine, enemy)
    already_enemy = find_captured(enemy, mine)
    unsafe = find_captured(enemy, moves)
    for point in ranked:
        if perf_counter() - started >= time_limit:
            break
        value = position_value(point)
        if neighbors(point, mine) >= 2:
            gained = find_captured(mine | {point}, enemy) - already_mine
            value += 1000 * len(gained)
        if neighbors(point, enemy) >= 2:
            # Если соперник закроет здесь кольцо, сколько мы потеряем?
            danger = find_captured(enemy | {point}, mine) - already_enemy
            value += 800 * len(danger)
        if point in unsafe:
            value -= 1200
        if value > best_value:
            best, best_value = point, value
    return best
