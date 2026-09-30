from .field import (
    active_fields,
    field_tiles,
    is_starter_phase,
    main_farmer_fields,
    planting_limit,
    second_farmer_fields,
    specialists_unlocked,
    total_planting_limit,
)
from .price_observer import CROPS, FIELD_CROPS, price_observer, recommend
from .workers import AnimalWorker, BerryWorker, CropWorker

SELL_BATCH_SIZE = 6
ENDGAME_DAY = 27
SPECIALISTS_START_DAY = 4
ANIMALS = ("GOOSE", "COW")


def market_orders(obs, recommendation):
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    market = []

    for crop in CROPS:
        amount = private["shed"].get(crop.name, 0)
        price = obs["market"]["prices"].get(crop.name, 0)
        should_sell = price_observer.is_high(crop, price) or obs["day"] >= ENDGAME_DAY
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


def should_hire_starter_helper(farm, day):
    tiles = field_tiles(farm, active_fields(day))
    return any(
        isinstance(tile, dict) and tile.get("kind") == "WEED" for tile in tiles.values()
    )


def crop_worker(day, fields, planting_crop):
    return CropWorker(fields, planting_limit(day), planting_crop)


def worker_roles(obs, planting_crop):
    farm = obs["farms"][obs["player"]]
    day = obs["day"]
    roles = [crop_worker(day, main_farmer_fields(day), planting_crop)]

    if is_starter_phase(day):
        if should_hire_starter_helper(farm, day):
            roles.append(crop_worker(day, second_farmer_fields(day), planting_crop))
        return roles

    roles.append(crop_worker(day, second_farmer_fields(day), planting_crop))
    if day < SPECIALISTS_START_DAY:
        return roles

    if specialists_unlocked(farm) and BerryWorker.should_hire(obs):
        roles.append(BerryWorker())
    for animal in ANIMALS:
        if AnimalWorker.should_hire(obs, animal):
            roles.append(AnimalWorker(animal))
    return roles


def hand_actions(obs, roles):
    farm = obs["farms"][obs["player"]]
    inventories = obs["private"]["inventories"]
    return [
        role.action(obs, tuple(hand), inventories[index + 1])
        for index, (role, hand) in enumerate(zip(roles[1:], farm["hands"]))
    ]


def specialist_market_orders(obs, farm):
    if obs["day"] < SPECIALISTS_START_DAY:
        return []

    orders = AnimalWorker.market_orders(obs)
    if specialists_unlocked(farm):
        orders.extend(BerryWorker.market_orders(obs))
    return orders


def hire_orders(roles, farm):
    missing_workers = len(roles) - 1 - len(farm["hands"])
    return [["HIRE"] for _ in range(max(0, missing_workers))]


def agent(obs):
    farm = obs["farms"][obs["player"]]
    price_observer.observe(obs)
    recommendation = recommend(obs, FIELD_CROPS)
    planting_crop = recommendation.crop.name if recommendation else None
    market = market_orders(obs, recommendation)
    roles = worker_roles(obs, planting_crop)
    market.extend(specialist_market_orders(obs, farm))
    market.extend(hire_orders(roles, farm))

    return {
        "farmer": roles[0].action(
            obs, tuple(farm["farmer"]), obs["private"]["inventories"][0]
        ),
        "hands": hand_actions(obs, roles),
        "market": market[:10],
    }
