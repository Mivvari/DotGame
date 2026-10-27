"""Проверка JSON и перевод списков из API в множества пар."""

from math import isfinite

from bot import choose_move
from core import find_captured


def read_position(data, first, second):
    if not isinstance(data, dict):
        raise ValueError("Ожидается JSON-объект")
    size = data.get("size", 100)
    if size is not None and (type(size) is not int or size < 1):
        raise ValueError("size должен быть положительным целым числом или null")

    def read_points(name):
        values = data.get(name)
        if not isinstance(values, list) or len(values) > 10000:
            raise ValueError(f"{name}: нужен список, не более 10000 точек")
        result = set()
        for point in values:
            if (not isinstance(point, list) or len(point) != 2
                    or any(type(value) is not int for value in point)):
                raise ValueError(f"{name}: каждая точка — пара целых чисел")
            x, y = point
            if size is not None and not (0 <= x < size and 0 <= y < size):
                raise ValueError(f"{name}: координаты должны быть от 0 до {size - 1}")
            if (x, y) in result:
                raise ValueError(f"{name}: точка {(x, y)} повторяется")
            result.add((x, y))
        return result

    mine, enemy = read_points(first), read_points(second)
    if mine & enemy:
        raise ValueError("Одна точка не может принадлежать двум игрокам")
    return mine, enemy, size


def move_response(data):
    mine, enemy, size = read_position(data, "me", "enemy")
    time_limit = data.get("time_limit", 0.5)
    if (type(time_limit) not in (int, float) or not isfinite(time_limit)
            or not 0 <= time_limit <= 2):
        raise ValueError("time_limit должен быть числом от 0 до 2 секунд")
    point = choose_move(mine, enemy, size, time_limit)
    if point is None:
        return {"error": "Поле заполнено: свободных ходов нет", "code": "board_full"}, 409
    return {"x": point[0], "y": point[1]}, 200


def score_response(data):
    blue, red, _ = read_position(data, "blue", "red")
    # В ответе называем цвет ЗАХВАЧЕННЫХ точек, как в задании.
    return {
        "blue_captured": sorted(find_captured(red, blue)),
        "red_captured": sorted(find_captured(blue, red)),
    }
