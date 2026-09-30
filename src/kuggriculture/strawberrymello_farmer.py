from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

from .board import move_or_act, nearest


FIELDS = (
    (2, 1),
    (3, 1),
    (4, 1),
    (4, 2),
    (3, 2),
    (2, 2),
)
SHED_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
CROPS_TO_GROW = ("STRAWBERRY", "MELON")
MIN_REVENUE_MULTIPLIER = 2
SELL_ALL_AFTER_DAY = 27


def _profitable_crops(prices):
    profitable = []
    for crop in CROPS_TO_GROW:
        crop_data = CROPS[crop]
        revenue = prices.get(crop, 0) * crop_data["max_yield"]
        seed_cost = crop_data["seed"]
        if revenue >= seed_cost * MIN_REVENUE_MULTIPLIER:
            profitable.append((revenue / seed_cost, crop))
    return [crop for _, crop in sorted(profitable, reverse=True)]


def _field_crop_counts(tiles):
    counts = {crop: 0 for crop in CROPS_TO_GROW}
    for x, y in FIELDS:
        tile = tiles[y][x]
        if isinstance(tile, dict) and tile.get("crop") in counts:
            counts[tile["crop"]] += 1
    return counts


def _is_harvestable(tile, day):
    crop_data = CROPS[tile["crop"]]
    if tile["crop"] == "MELON":
        age = day - tile["planted_day"]
        return tile.get("yield_units", 0) >= crop_data["max_yield"] or age >= crop_data["max_yield_day"]
    return tile.get("yield_units", 0) > 0


def _crop_targets(crops):
    if not crops:
        return {}
    base, remainder = divmod(len(FIELDS), len(crops))
    return {crop: base + int(index < remainder) for index, crop in enumerate(crops)}


def _plant_crop(obs):
    crops = _profitable_crops(obs["market"].get("prices", {}))
    targets = _crop_targets(crops)
    counts = _field_crop_counts(obs["farms"][obs["player"]]["tiles"])
    seeds = obs["private"]["seeds"]
    eligible = [crop for crop in crops if seeds.get(crop, 0) > 0 and counts[crop] < targets[crop]]
    return eligible[0] if eligible else None


def has_crop_work(obs):
    farm = obs["farms"][obs["player"]]
    tiles = farm["tiles"]
    for x, y in FIELDS:
        tile = tiles[y][x]
        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") in CROPS_TO_GROW
            and (_is_harvestable(tile, obs["day"]) or not tile.get("watered_today", False))
        ):
            return True
    return False


def should_hire(obs):
    if has_crop_work(obs):
        return True

    farm = obs["farms"][obs["player"]]
    crops = _profitable_crops(obs["market"].get("prices", {}))
    if not crops:
        return False

    targets = _crop_targets(crops)
    counts = _field_crop_counts(farm["tiles"])
    empty_count = sum(farm["tiles"][y][x] is None for x, y in FIELDS)
    seeds = obs["private"]["seeds"]
    return empty_count > 0 and any(
        counts[crop] < targets[crop]
        and (seeds.get(crop, 0) > 0 or farm["money"] >= CROPS[crop]["seed"])
        for crop in crops
    )


def market_orders(obs):
    private = obs["private"]
    prices = obs["market"].get("prices", {})
    orders = []

    profitable_crops = _profitable_crops(prices)
    for crop in CROPS_TO_GROW:
        quantity = private["shed"].get(crop, 0)
        if quantity and obs["day"] >= SELL_ALL_AFTER_DAY:
            orders.append(["SELL", crop, quantity])
        elif quantity and crop in profitable_crops:
            orders.append(["SELL", crop, 1])

    farm = obs["farms"][obs["player"]]
    if not profitable_crops:
        return orders

    targets = _crop_targets(profitable_crops)
    counts = _field_crop_counts(farm["tiles"])
    empty_count = sum(farm["tiles"][y][x] is None for x, y in FIELDS)
    budget = farm["money"]
    for crop in profitable_crops:
        seed_cost = CROPS[crop]["seed"]
        seeds = private["seeds"].get(crop, 0)
        needed = max(0, targets[crop] - counts[crop] - seeds)
        quantity = min(needed, empty_count, int(budget // seed_cost))
        if quantity > 0:
            orders.append(["BUY_SEED", crop, quantity])
            empty_count -= quantity
            budget -= quantity * seed_cost
    return orders


def action(obs, hand_position, inventory):
    position = tuple(hand_position)
    if sum(inventory.values()) >= 20:
        target = nearest(position, SHED_ACCESS)
        return move_or_act(position, target, ["DROP"])

    farm = obs["farms"][obs["player"]]
    tiles = farm["tiles"]
    candidates = []
    for x, y in FIELDS:
        tile = tiles[y][x]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in CROPS_TO_GROW:
            if _is_harvestable(tile, obs["day"]):
                candidates.append((0, (x, y), ["HARVEST"]))
            elif not tile.get("watered_today", False):
                candidates.append((1, (x, y), ["WATER"]))

    crop = _plant_crop(obs)
    if crop and obs["private"]["seeds"].get(crop, 0) > 0:
        for x, y in FIELDS:
            if tiles[y][x] is None:
                candidates.append((2, (x, y), ["PLANT", crop]))

    if not candidates:
        return ["PASS"]

    priority = min(candidate[0] for candidate in candidates)
    targets = [candidate for candidate in candidates if candidate[0] == priority]
    target = nearest(position, [candidate[1] for candidate in targets])
    task = next(candidate[2] for candidate in targets if candidate[1] == target)
    return move_or_act(position, target, task)