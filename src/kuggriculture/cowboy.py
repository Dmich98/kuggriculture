from .livestock import action as livestock_action
from .livestock import product_market_orders, should_hire as livestock_should_hire


ANIMAL = "COW"


def action(obs, hand_position, inventory):
    return livestock_action(obs, hand_position, inventory, ANIMAL)


def should_hire(obs):
    return livestock_should_hire(obs, ANIMAL)


def market_orders(obs):
    return product_market_orders(obs, ANIMAL)