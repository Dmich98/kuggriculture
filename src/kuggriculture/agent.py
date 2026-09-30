from .farm_worker import action as worker_action
from .field import (
    active_fields,
    field_tiles,
    is_starter_phase,
    main_farmer_fields,
    planting_limit,
    second_farmer_fields,
    total_planting_limit,
)
from .price_observer import CROPS, price_observer, recommend

SELL_BATCH_SIZE = 6


def market_orders(obs, recommendation):
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    market = []

    for crop in CROPS:
        amount = private["shed"].get(crop.name, 0)
        price = obs["market"]["prices"].get(crop.name, 0)
        should_sell = price_observer.is_high(crop, price) or obs["day"] >= 27
        if amount and should_sell:
            market.append(["SELL", crop.name, min(amount, SELL_BATCH_SIZE)])

    tiles = field_tiles(farm, active_fields(obs["day"]))
    empty_count = sum(tile is None for tile in tiles.values())
    seeds_needed = min(empty_count, total_planting_limit(obs["day"]))
    if recommendation:
        crop_name = recommendation.crop.name
        seeds = private["seeds"].get(crop_name, 0)
        if seeds_needed > seeds:
            market.append(["BUY_SEED", crop_name, seeds_needed - seeds])

    return market


def should_hire_second_farmer(farm, day):
    if farm["hands"] or farm["hires_today"] != 0:
        return False

    if not is_starter_phase(day):
        return True

    tiles = field_tiles(farm, active_fields(day))
    return any(
        isinstance(tile, dict) and tile.get("kind") == "WEED" for tile in tiles.values()
    )


def second_farmer_actions(obs, fields, planting_crop):
    farm = obs["farms"][obs["player"]]
    inventories = obs["private"]["inventories"]

    return [
        worker_action(
            obs,
            tuple(hand),
            inventories[index + 1],
            fields,
            planting_limit(obs["day"]),
            planting_crop,
        )
        for index, hand in enumerate(farm["hands"])
    ]


def agent(obs):
    farm = obs["farms"][obs["player"]]
    price_observer.observe(obs)
    recommendation = recommend(obs)
    planting_crop = recommendation.crop.name if recommendation else None
    market = market_orders(obs, recommendation)

    if should_hire_second_farmer(farm, obs["day"]):
        market.append(["HIRE"])

    return {
        "farmer": worker_action(
            obs,
            tuple(farm["farmer"]),
            obs["private"]["inventories"][0],
            main_farmer_fields(obs["day"]),
            planting_limit(obs["day"]),
            planting_crop,
        ),
        "hands": second_farmer_actions(
            obs,
            second_farmer_fields(obs["day"]),
            planting_crop,
        ),
        "market": market,
    }
