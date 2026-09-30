from .carrot_farmer import action as farmer_action
from .carrot_farmer import market_orders, seed_order
from .chickenfarmer import action as chickenfarmer_action
from .chickenfarmer import market_orders as chickenfarmer_market_orders
from .chickenfarmer import should_hire as should_hire_chickenfarmer
from .cowboy import action as cowboy_action
from .cowboy import market_orders as cowboy_market_orders
from .cowboy import should_hire as should_hire_cowboy
from .livestock import market_orders as livestock_market_orders
from .strawberrymello_farmer import action as strawberrymello_action
from .strawberrymello_farmer import should_hire as should_hire_strawberrymello
from .weed_keeper import actions as weed_keeper_actions
from .weed_keeper import find_weeds, should_hire


def _market_priority(order):
    if order[0] == "SELL":
        return 0
    if order[0] == "BUY_LAND":
        return 1
    if order[0] == "BUY_ANIMAL":
        return 2
    if order[0] == "HIRE":
        return 3
    if order[0] == "BUY_PRODUCT":
        return 4
    if order[0] == "BUY_SEED" and order[1] == "WHEAT":
        return 5
    return 6


def agent(obs):
    farm = obs["farms"][obs["player"]]
    weeds = find_weeds(farm["tiles"])
    market = market_orders(obs)

    keeper_needed = should_hire(farm, weeds)
    strawberrymello_needed = should_hire_strawberrymello(obs)
    desired_hires = 2 if strawberrymello_needed else int(keeper_needed)
    if should_hire_chickenfarmer(obs):
        desired_hires = max(desired_hires, 3)
    if should_hire_cowboy(obs):
        desired_hires = max(desired_hires, 4)

    market.extend(chickenfarmer_market_orders(obs))
    market.extend(cowboy_market_orders(obs))
    market.extend(livestock_market_orders(obs))

    hire_budget = farm["money"]
    for hire_index in range(farm["hires_today"], desired_hires):
        first, second = 1, 1
        for _ in range(hire_index):
            first, second = second, first + second
        if hire_budget < first:
            break
        market.append(["HIRE"])
        hire_budget -= first

    order = seed_order(obs)
    if order:
        market.append(order)

    hands = [["PASS"] for _ in farm["hands"]]
    if hands:
        hands[0] = weed_keeper_actions(farm["hands"][:1], weeds)[0]
    if len(hands) > 1:
        inventories = obs["private"].get("inventories", [])
        inventory = inventories[2] if len(inventories) > 2 else {}
        hands[1] = strawberrymello_action(obs, farm["hands"][1], inventory)
    if len(hands) > 2:
        inventories = obs["private"].get("inventories", [])
        inventory = inventories[3] if len(inventories) > 3 else {}
        hands[2] = chickenfarmer_action(obs, farm["hands"][2], inventory)
    if len(hands) > 3:
        inventories = obs["private"].get("inventories", [])
        inventory = inventories[4] if len(inventories) > 4 else {}
        hands[3] = cowboy_action(obs, farm["hands"][3], inventory)

    market.sort(key=_market_priority)
    market = market[:10]

    return {
        "farmer": farmer_action(obs),
        "hands": hands,
        "market": market,
    }
