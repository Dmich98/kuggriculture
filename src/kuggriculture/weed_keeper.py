from .board import move_or_act, nearest


def find_weeds(tiles):
    return [
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if isinstance(tile, dict) and tile.get("kind") == "WEED"
    ]


def should_hire(farm, weeds):
    return bool(weeds) and not farm["hands"] and farm["hires_today"] == 0


def actions(hands, weeds):
    result = []
    for hand in hands:
        if not weeds:
            result.append(["PASS"])
            continue

        target = nearest(tuple(hand), weeds)
        result.append(move_or_act(tuple(hand), target, ["DIG"]))
    return result
