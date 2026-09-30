from .carrot_farmer import action as farmer_action
from .carrot_farmer import market_orders, seed_order
from .weed_keeper import actions as weed_keeper_actions
from .weed_keeper import find_weeds, should_hire


def agent(obs):
    farm = obs["farms"][obs["player"]]
    weeds = find_weeds(farm["tiles"])
    market = market_orders(obs)

    if should_hire(farm, weeds):
        market.append(["HIRE"])

    order = seed_order(obs)
    if order:
        market.append(order)

    return {
        "farmer": farmer_action(obs),
        "hands": weed_keeper_actions(farm["hands"], weeds),
        "market": market,
    }
