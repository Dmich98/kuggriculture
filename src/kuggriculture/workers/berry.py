from dataclasses import dataclass

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

from ..field import BERRY_FIELD, specialists_unlocked
from .base import Worker


@dataclass(frozen=True)
class BerryWorker(Worker):
    crops = ("STRAWBERRY", "MELON")

    @classmethod
    def choices(cls, prices):
        return sorted(
            (
                crop
                for crop in cls.crops
                if prices.get(crop, 0) * CROPS[crop]["max_yield"]
                >= 2 * CROPS[crop]["seed"]
            ),
            key=lambda crop: prices.get(crop, 0) / CROPS[crop]["seed"],
            reverse=True,
        )

    @classmethod
    def should_hire(cls, obs):
        farm = obs["farms"][obs["player"]]
        if not specialists_unlocked(farm):
            return False
        return bool(cls.choices(obs["market"]["prices"])) or any(
            isinstance(farm["tiles"][y][x], dict)
            and farm["tiles"][y][x].get("crop") in cls.crops
            for x, y in BERRY_FIELD
        )

    @classmethod
    def market_orders(cls, obs):
        private = obs["private"]
        choices = cls.choices(obs["market"]["prices"])
        orders = [
            ["SELL", crop, amount]
            for crop in cls.crops
            if (amount := private["shed"].get(crop, 0))
            and (obs["day"] >= 27 or crop in choices)
        ]
        if not choices:
            return orders
        crop = choices[0]
        farm = obs["farms"][obs["player"]]
        empty = sum(farm["tiles"][y][x] is None for x, y in BERRY_FIELD)
        seeds = private["seeds"].get(crop, 0)
        if quantity := min(
            max(0, empty - seeds), int(farm["money"] // CROPS[crop]["seed"])
        ):
            orders.append(["BUY_SEED", crop, quantity])
        return orders

    def action(self, obs, position, inventory):
        tiles = obs["farms"][obs["player"]]["tiles"]
        choices = self.choices(obs["market"]["prices"])
        if sum(inventory.values()) >= 20:
            return self.move_or_act(position, (4, 4), ["DROP"])
        tasks = []
        for field in BERRY_FIELD:
            tile = tiles[field[1]][field[0]]
            if not isinstance(tile, dict) or tile.get("crop") not in self.crops:
                continue
            if tile.get("yield_units", 0):
                tasks.append((0, field, ["HARVEST"]))
            elif not tile.get("watered_today", False):
                tasks.append((1, field, ["WATER"]))
        if choices and obs["private"]["seeds"].get(choices[0], 0):
            tasks.extend(
                (2, field, ["PLANT", choices[0]])
                for field in BERRY_FIELD
                if tiles[field[1]][field[0]] is None
            )
        return self._task_action(position, tasks)

    def _task_action(self, position, tasks):
        if not tasks:
            return ["PASS"]
        priority = min(task[0] for task in tasks)
        tasks = [task for task in tasks if task[0] == priority]
        target = self.nearest(position, [task[1] for task in tasks])
        return self.move_or_act(
            position, target, next(task[2] for task in tasks if task[1] == target)
        )
