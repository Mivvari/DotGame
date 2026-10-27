"""Бот против бота: python simulate.py --moves 60 --size 100."""

import argparse

from bot import choose_move
from core import find_captured, is_free


def simulate(size=100, moves=60, time_limit=0.05):
    blue, red = set(), set()
    played = 0
    for turn in range(moves):
        mine, enemy = (blue, red) if turn % 2 == 0 else (red, blue)
        point = choose_move(mine, enemy, size, time_limit)
        if point is None:
            break
        if not is_free(*point, mine, enemy, size):
            raise RuntimeError(f"Бот предложил недопустимый ход: {point}")
        mine.add(point)
        played += 1
    result = {
        "moves": played,
        "blue_score": len(find_captured(blue, red)),
        "red_score": len(find_captured(red, blue)),
    }
    print(f"Ходов: {played}. Счёт — синие {result['blue_score']} : {result['red_score']} красные")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Проверка игры двух ботов")
    parser.add_argument("--size", default="100", help="Размер поля или none для бесконечного")
    parser.add_argument("--moves", type=int, default=60)
    parser.add_argument("--time-limit", type=float, default=0.05)
    args = parser.parse_args()
    size = None if args.size.lower() == "none" else int(args.size)
    if size is not None and size < 1:
        parser.error("Размер должен быть положительным")
    if args.moves < 0:
        parser.error("Число ходов не может быть отрицательным")
    simulate(size, args.moves, args.time_limit)
