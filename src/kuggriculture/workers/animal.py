from dataclasses import dataclass
from typing import ClassVar

from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS

from ..field import LIVESTOCK_SITES
from ..price_observer import (
    ANIMAL_PLANS,
    MARKET_PRODUCT_BY_NAME,
    price_observer,
    recommend_animal,
)
from .base import Worker


@dataclass(frozen=True)
class AnimalWorker(Worker):
    animal: str
    animals: ClassVar = ("GOOSE", "COW")
    targets: ClassVar = {"GOOSE": 2, "COW": 2}

    @classmethod
    def count(cls, obs, animal):
        private = obs["private"]
        placed = sum(
            isinstance(tile, dict) and tile.get("animal") == animal
            for row in obs["farms"][obs["player"]]["tiles"]
            for tile in row
        )
        return (
            placed
            + private["shed"].get(animal, 0)
            + sum(items.get(animal, 0) for items in private["inventories"])
        )

    @classmethod
    def should_hire(cls, obs, animal):
        return cls.count(obs, animal) > 0

    @classmethod
    def market_orders(cls, obs):
        farm, private = obs["farms"][obs["player"]], obs["private"]
        animal_count = sum(cls.count(obs, animal) for animal in cls.animals)
        orders = []
        plan = next(
            (
                candidate
                for candidate in ANIMAL_PLANS
                if 0 < cls.count(obs, candidate.animal) < candidate.quantity
            ),
            None,
        )
        if plan is None:
            completed_animals = {
                candidate.animal
                for candidate in ANIMAL_PLANS
                if cls.count(obs, candidate.animal) >= candidate.quantity
            }
            plan = recommend_animal(obs, completed_animals)
        if plan and cls.count(obs, plan.animal) < plan.quantity:
            remaining_purchase_cost = plan.purchase_cost * (
                plan.quantity - cls.count(obs, plan.animal)
            )
            if farm["money"] >= remaining_purchase_cost + 200:
                orders.append(["BUY_ANIMAL", plan.animal, 1])
        for animal in cls.animals:
            product = ANIMALS[animal]["product"]
            if (amount := private["shed"].get(product, 0)) and (
                obs["day"] >= 27
                or price_observer.is_high(
                    MARKET_PRODUCT_BY_NAME[product],
                    obs["market"]["prices"].get(product, 0),
                )
            ):
                orders.append(["SELL", product, amount])

        wheat = private["shed"].get("WHEAT", 0)
        if animal_count and wheat < animal_count * 2:
            orders.append(["BUY_PRODUCT", "WHEAT", animal_count * 2 - wheat])
        return orders

    def action(self, obs, position, inventory):
        farm = obs["farms"][obs["player"]]
        half = len(farm["tiles"]) // 2
        sites = LIVESTOCK_SITES[self.animal]
        tiles, structure = farm["tiles"], ANIMALS[self.animal]["structure"]
        access = (
            (half - 1, half - 1),
            (half, half - 1),
            (half - 1, half),
            (half, half),
        )
        for site in sites:
            tile = tiles[site[1]][site[0]]
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                return self.move_or_act(position, site, ["DIG"])
        for site in sites:
            tile = tiles[site[1]][site[0]]
            if (
                isinstance(tile, dict)
                and tile.get("kind") == structure
                and "animal" not in tile
            ):
                if inventory.get(self.animal, 0):
                    return self.move_or_act(position, site, ["PLACE", self.animal])
                if obs["private"]["shed"].get(self.animal, 0):
                    return self.move_or_act(
                        position,
                        self.nearest(position, access),
                        ["PICKUP", self.animal, 1],
                    )
        for site in sites:
            if tiles[site[1]][site[0]] is None:
                return self.move_or_act(
                    position,
                    site,
                    ["BUILD_COOP"] if self.animal == "GOOSE" else ["BUILD_PASTURE"],
                )
        for site in sites:
            tile = tiles[site[1]][site[0]]
            if not isinstance(tile, dict) or tile.get("animal") != self.animal:
                continue
            if not tile.get("fed_today", False):
                if inventory.get("WHEAT", 0):
                    return self.move_or_act(position, site, ["FEED"])
                if obs["private"]["shed"].get("WHEAT", 0):
                    return self.move_or_act(
                        position,
                        self.nearest(position, access),
                        ["PICKUP", "WHEAT", self.targets[self.animal]],
                    )
            if tile.get("yield_units", 0):
                return self.move_or_act(position, site, ["HARVEST"])
            if not tile.get("cared_today", False):
                return self.move_or_act(position, site, ["CARE"])
        return ["PASS"]
