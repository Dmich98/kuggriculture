from .board import move_or_act, nearest
from .strawberrymello_farmer import market_orders as strawberrymello_market_orders


FIELDS = [
    (2, 3),
    (3, 3),
    (4, 3),
    (2, 4),
    (3, 4),
    (4, 4),
]
SHED = (4, 4)
MIN_SELL_PRICE = 30


def field_tiles(farm):
    return {field: farm["tiles"][field[1]][field[0]] for field in FIELDS}


def market_orders(obs):
    private = obs["private"]
    carrots = private["shed"].get("CARROT", 0)
    price = obs["market"]["prices"].get("CARROT", 0)

    orders = []
    if carrots and (price >= MIN_SELL_PRICE or obs["day"] >= 27):
        orders.append(["SELL", "CARROT", carrots])
    orders.extend(strawberrymello_market_orders(obs))
    return orders


def action(obs):
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    position = tuple(farm["farmer"])
    fields = field_tiles(farm)

    if private["inventories"][0].get("CARROT", 0):
        return move_or_act(position, SHED, ["DROP"])

    ripe = [
        field
        for field, tile in fields.items()
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "CARROT"
        and obs["day"] - tile["planted_day"] >= 3
    ]
    if ripe:
        target = nearest(position, ripe)
        return move_or_act(position, target, ["HARVEST"])

    thirsty = [
        field
        for field, tile in fields.items()
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "CARROT"
        and not tile["watered_today"]
    ]
    if thirsty:
        target = nearest(position, thirsty)
        return move_or_act(position, target, ["WATER"])

    empty = [field for field, tile in fields.items() if tile is None]
    if not empty:
        return ["PASS"]

    if private["seeds"].get("CARROT", 0) == 0:
        return ["PASS"]

    target = nearest(position, empty)
    return move_or_act(position, target, ["PLANT", "CARROT"])


def seed_order(obs):
    farm = obs["farms"][obs["player"]]
    empty_count = sum(tile is None for tile in field_tiles(farm).values())
    seeds = obs["private"]["seeds"].get("CARROT", 0)

    if empty_count and seeds == 0:
        return ["BUY_SEED", "CARROT", empty_count]
    return None
