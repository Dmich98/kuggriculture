from .field import SHED, field_tiles
from .navigation import move_or_act, nearest
from .price_observer import CROP_BY_NAME


def action(obs, position, inventory, fields, plant_limit, planting_crop):
    tiles = field_tiles(obs["farms"][obs["player"]], fields)

    if any(inventory.get(crop_name, 0) for crop_name in CROP_BY_NAME):
        return move_or_act(position, SHED, ["DROP"])

    ripe = [
        field
        for field, tile in tiles.items()
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") in CROP_BY_NAME
        and obs["day"] - tile["planted_day"] >= CROP_BY_NAME[tile["crop"]].harvest_day
    ]
    if ripe:
        return move_or_act(position, nearest(position, ripe), ["HARVEST"])

    thirsty = [
        field
        for field, tile in tiles.items()
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") in CROP_BY_NAME
        and not tile["watered_today"]
    ]
    if thirsty:
        return move_or_act(position, nearest(position, thirsty), ["WATER"])

    empty = [field for field, tile in tiles.items() if tile is None]
    if planting_crop is None:
        return ["PASS"]

    seeds_available = obs["private"]["seeds"].get(planting_crop, 0)

    if plant_limit is not None:
        planted_today = sum(
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile["planted_day"] == obs["day"]
            for tile in tiles.values()
        )
        if planted_today >= plant_limit:
            return ["PASS"]

    if empty and seeds_available:
        return move_or_act(position, nearest(position, empty), ["PLANT", planting_crop])

    if not seeds_available:
        return ["PASS"]

    weeds = [
        field
        for field, tile in tiles.items()
        if isinstance(tile, dict) and tile.get("kind") == "WEED"
    ]
    if weeds:
        return move_or_act(position, nearest(position, weeds), ["DIG"])

    return ["PASS"]
