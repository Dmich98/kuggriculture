from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS

from .board import move_or_act, nearest


ANIMALS_TO_KEEP = ("GOOSE", "COW")
ANIMAL_TARGETS = {"GOOSE": 2, "COW": 1}
LAND_COST = 1000
MIN_REVENUE_MULTIPLIER = 1.5
SELL_ALL_AFTER_DAY = 27
TARGET_WHEAT_PLANTS = 6
WHEAT_SEED_TARGET_PER_HAND = 3
LAND_CASH_RESERVE = 200
HAND_HIRE_RESERVE = 7
ANIMAL_PURCHASE_LIMIT_PER_TURN = 1


def _is_profitable(obs, animal):
    prices = obs["market"].get("prices", {})
    product = ANIMALS[animal]["product"]
    feed_units = 1 if animal == "GOOSE" else 2
    feed_cost = prices.get("WHEAT", 25) * feed_units
    return prices.get(product, 0) >= feed_cost * MIN_REVENUE_MULTIPLIER


def _animal_site(animal, board_size):
    half = board_size // 2
    y = max(0, half - 2)
    if animal == "GOOSE":
        return tuple((x, y) for x in range(half, min(board_size, half + ANIMAL_TARGETS[animal])))
    return tuple((x, y) for x in range(max(half, board_size - ANIMAL_TARGETS[animal]), board_size))


def _wheat_fields(board_size):
    half = board_size // 2
    return [
        (x, y)
        for y in range(max(0, half - 2))
        for x in range(half, board_size)
    ]


def _shed_access_tiles(board_size):
    half = board_size // 2
    return (
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    )


def _animal_positions(farm):
    positions = {animal: [] for animal in ANIMALS_TO_KEEP}
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("animal") in positions:
                positions[tile["animal"]].append((x, y))
    return positions


def _animal_count(obs, animal):
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    placed = len(_animal_positions(farm)[animal])
    count = private.get("shed", {}).get(animal, 0)
    carried = sum(inventory.get(animal, 0) for inventory in private.get("inventories", []))
    return placed + count + carried


def _has_animal(obs, animal):
    return _animal_count(obs, animal) > 0


def should_buy_land(obs):
    farm = obs["farms"][obs["player"]]
    if "NE" in farm.get("unlocked_quadrants", ["NW"]):
        return False

    profitable = [animal for animal in ANIMALS_TO_KEEP if _is_profitable(obs, animal)]
    if not profitable or obs.get("day", 0) > 14:
        return False

    wheat_price = obs["market"].get("prices", {}).get("WHEAT", 25)
    startup_animals = sum(ANIMAL_TARGETS[animal] for animal in profitable)
    startup_cost = LAND_COST
    startup_cost += sum(ANIMALS[animal]["cost"] * ANIMAL_TARGETS[animal] for animal in profitable)
    startup_cost += startup_animals * 2 * wheat_price
    startup_cost += TARGET_WHEAT_PLANTS * CROPS["WHEAT"]["seed"]
    startup_cost += LAND_CASH_RESERVE + HAND_HIRE_RESERVE
    return farm["money"] >= startup_cost


def market_orders(obs):
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    orders = []
    land_pending = should_buy_land(obs)
    land_unlocked = "NE" in farm.get("unlocked_quadrants", ["NW"]) or land_pending

    if land_pending:
        orders.append(["BUY_LAND"])
    if not land_unlocked:
        return orders

    profitable = [animal for animal in ANIMALS_TO_KEEP if _is_profitable(obs, animal)]
    budget = farm["money"] - (LAND_COST if land_pending else 0) - HAND_HIRE_RESERVE
    for animal in ANIMALS_TO_KEEP:
        if animal in profitable:
            missing = max(0, ANIMAL_TARGETS[animal] - _animal_count(obs, animal))
            quantity = min(
                missing,
                ANIMAL_PURCHASE_LIMIT_PER_TURN,
                int(max(0, budget) // ANIMALS[animal]["cost"]),
            )
            if quantity:
                orders.append(["BUY_ANIMAL", animal, quantity])
                budget -= quantity * ANIMALS[animal]["cost"]

    animal_count = sum(_animal_count(obs, animal) for animal in ANIMALS_TO_KEEP)
    animal_count += sum(order[2] for order in orders if order[0] == "BUY_ANIMAL")
    if animal_count == 0:
        return orders

    inventory = private.get("inventories", [])
    wheat_on_hand = sum(unit_inventory.get("WHEAT", 0) for unit_inventory in inventory)
    wheat_available = private.get("shed", {}).get("WHEAT", 0) + wheat_on_hand
    feed_target = animal_count * 2
    feed_needed = max(0, feed_target - wheat_available)
    wheat_price = max(1, obs["market"].get("prices", {}).get("WHEAT", 25))
    feed_quantity = min(feed_needed, int(max(0, budget) // wheat_price))
    if feed_quantity:
        orders.append(["BUY_PRODUCT", "WHEAT", feed_quantity])
        budget -= feed_quantity * wheat_price

    fields = _wheat_fields(len(farm["tiles"]))
    tiles = farm["tiles"]
    planted = sum(
        isinstance(tiles[y][x], dict)
        and tiles[y][x].get("kind") == "PLANT"
        and tiles[y][x].get("crop") == "WHEAT"
        for x, y in fields
    )
    seed_count = private.get("seeds", {}).get("WHEAT", 0)
    empty_count = sum(tiles[y][x] is None for x, y in fields)
    seed_needed = max(0, min(TARGET_WHEAT_PLANTS, planted + empty_count) - planted - seed_count)
    seed_quantity = min(seed_needed, int(max(0, budget) // CROPS["WHEAT"]["seed"]))
    if seed_quantity:
        orders.append(["BUY_SEED", "WHEAT", seed_quantity])
    return orders


def should_hire(obs, animal):
    farm = obs["farms"][obs["player"]]
    if "NE" not in farm.get("unlocked_quadrants", ["NW"]):
        return False
    return _has_animal(obs, animal) or _is_profitable(obs, animal)


def product_market_orders(obs, animal):
    product = ANIMALS[animal]["product"]
    quantity = obs["private"].get("shed", {}).get(product, 0)
    if not quantity:
        return []
    if obs.get("day", 0) >= SELL_ALL_AFTER_DAY:
        return [["SELL", product, quantity]]
    if _is_profitable(obs, animal):
        return [["SELL", product, 1]]
    return []


def _wheat_action(obs, position, inventory, fields, urgent):
    farm = obs["farms"][obs["player"]]
    tiles = farm["tiles"]
    day = obs["day"]
    seed_count = obs["private"]["seeds"].get("WHEAT", 0)
    planted = sum(
        isinstance(tiles[y][x], dict)
        and tiles[y][x].get("kind") == "PLANT"
        and tiles[y][x].get("crop") == "WHEAT"
        for x, y in fields
    )
    candidates = []

    for x, y in fields:
        tile = tiles[y][x]
        task = None
        priority = 0
        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            task = ["DIG"]
            priority = 0
        elif isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "WHEAT":
            age = day - tile["planted_day"]
            yield_units = tile.get("yield_units", 0)
            if yield_units > 0 and (age >= CROPS["WHEAT"]["max_yield_day"] or urgent):
                task = ["HARVEST"]
                priority = 1
            elif not tile.get("watered_today", False) and age <= CROPS["WHEAT"]["max_yield_day"]:
                task = ["WATER"]
                priority = 2
            elif yield_units > 0 and age >= CROPS["WHEAT"]["first_yield_day"]:
                task = ["HARVEST"]
                priority = 3
        elif tile is None and seed_count > 0 and planted < WHEAT_SEED_TARGET_PER_HAND:
            task = ["PLANT", "WHEAT"]
            priority = 4

        if task:
            distance = abs(x - position[0]) + abs(y - position[1])
            candidates.append((priority, distance, (x, y), task))

    if not candidates:
        return ["PASS"]
    _, _, target, task = min(candidates)
    return move_or_act(position, target, task)


def action(obs, hand_position, inventory, animal):
    farm = obs["farms"][obs["player"]]
    board_size = len(farm["tiles"])
    if "NE" not in farm.get("unlocked_quadrants", ["NW"]):
        return ["PASS"]

    position = tuple(hand_position)
    sites = _animal_site(animal, board_size)
    structure = ANIMALS[animal]["structure"]
    if not sites or any(farm["tiles"][y][x] == "LOCKED" for x, y in sites):
        return ["PASS"]

    fields = _wheat_fields(board_size)
    field_split = len(fields) // 2
    assigned_fields = fields[:field_split] if animal == "GOOSE" else fields[field_split:]
    tiles = farm["tiles"]
    private = obs["private"]
    access_tiles = _shed_access_tiles(board_size)
    build_action = ["BUILD_COOP"] if animal == "GOOSE" else ["BUILD_PASTURE"]
    setup_tasks = []
    open_structures = []

    for site in sites:
        x, y = site
        tile = tiles[y][x]
        if tile is None:
            setup_tasks.append((0, site, build_action))
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            setup_tasks.append((0, site, ["DIG"]))
        elif isinstance(tile, dict) and tile.get("kind") == structure and "animal" not in tile:
            open_structures.append(site)

    if setup_tasks:
        _, target, task = min(setup_tasks, key=lambda item: (item[0], abs(item[1][0] - position[0]) + abs(item[1][1] - position[1])))
        return move_or_act(position, target, task)

    if open_structures:
        if inventory.get(animal, 0) > 0:
            target = nearest(position, open_structures)
            return move_or_act(position, target, ["PLACE", animal])
        if private.get("shed", {}).get(animal, 0) > 0:
            access = nearest(position, access_tiles)
            if position in access_tiles:
                return ["PICKUP", animal, 1]
            return move_or_act(position, access, ["PICKUP", animal, 1])

    occupied_sites = [
        (site, tiles[site[1]][site[0]])
        for site in sites
        if isinstance(tiles[site[1]][site[0]], dict)
        and tiles[site[1]][site[0]].get("animal") == animal
    ]
    tasks = []
    urgent_feed = False
    wheat_in_hand = inventory.get("WHEAT", 0) > 0
    wheat_in_shed = private.get("shed", {}).get("WHEAT", 0) > 0

    for site, tile in occupied_sites:
        if not tile.get("fed_today", False):
            if wheat_in_hand:
                tasks.append((0, site, ["FEED"]))
            elif wheat_in_shed:
                access = nearest(position, access_tiles)
                tasks.append((0, access, ["PICKUP", "WHEAT", 1]))
            else:
                urgent_feed = True
        elif tile.get("yield_units", 0) > 0:
            tasks.append((1, site, ["HARVEST"]))
        elif tile.get("fertilizer_available", False):
            tasks.append((2, site, ["COLLECT_FERTILIZER"]))
        elif not tile.get("cared_today", False):
            tasks.append((3, site, ["CARE"]))

    product = ANIMALS[animal]["product"]
    if inventory.get(product, 0) >= 8:
        access = nearest(position, access_tiles)
        return move_or_act(position, access, ["DROP"])

    if tasks:
        priority = min(task[0] for task in tasks)
        highest_priority = [task for task in tasks if task[0] == priority]
        target = nearest(position, [task[1] for task in highest_priority])
        task = next(task[2] for task in highest_priority if task[1] == target)
        return move_or_act(position, target, task)

    return _wheat_action(obs, position, inventory, assigned_fields, urgent=urgent_feed)