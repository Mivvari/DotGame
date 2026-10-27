"""Правила игры. Позиция — два множества пар (x, y)."""

from collections import deque

Point = tuple[int, int]
NEIGHBORS = tuple(
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy
)
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def is_free(x, y, mine, enemy, size=100):
    """Можно ли поставить точку в это место?"""
    if type(x) is not int or type(y) is not int:
        return False
    if size is not None and not (0 <= x < size and 0 <= y < size):
        return False
    return (x, y) not in mine and (x, y) not in enemy


def candidate_moves(mine, enemy, size=100, radius=1):
    """Свободные места рядом с точками обоих игроков."""
    if type(radius) is not int or radius < 1:
        raise ValueError("Радиус должен быть положительным целым числом")
    occupied = mine | enemy
    if not occupied:
        center = 0 if size is None else size // 2
        return {(center, center)} if is_free(center, center, mine, enemy, size) else set()
    return {
        (x + dx, y + dy)
        for x, y in occupied
        for dx in range(-radius, radius + 1)
        for dy in range(-radius, radius + 1)
        if is_free(x + dx, y + dy, mine, enemy, size)
    }


def find_captured(walls, targets):
    """Чужие точки, до которых не дошла вода снаружи забора.

    Соседи забора — по восьми направлениям, вода идёт только по четырём.
    Несвязанные заборы проверяем отдельно: даже координаты в миллиард
    не заставят нас обходить миллиард пустых клеток между ними.
    """
    remaining = set(walls)
    targets = set(targets) - walls
    captured = set()
    while remaining and targets - captured:
        seed = remaining.pop()
        fence = {seed}
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for dx, dy in NEIGHBORS:
                point = (x + dx, y + dy)
                if point in remaining:
                    remaining.remove(point)
                    fence.add(point)
                    stack.append(point)
        if len(fence) < 4:
            continue
        left = min(x for x, _ in fence) - 1
        right = max(x for x, _ in fence) + 1
        top = min(y for _, y in fence) - 1
        bottom = max(y for _, y in fence) + 1
        inside = {
            (x, y) for x, y in targets - captured
            if left < x < right and top < y < bottom
        }
        if not inside:
            continue
        wet = {(left, top)}
        queue = deque(wet)
        while queue:
            x, y = queue.popleft()
            for dx, dy in SIDES:
                point = (x + dx, y + dy)
                nx, ny = point
                if (left <= nx <= right and top <= ny <= bottom
                        and point not in fence and point not in wet):
                    wet.add(point)
                    queue.append(point)
        captured.update(inside - wet)
    return captured
