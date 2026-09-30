from dataclasses import dataclass

from ..field import SHED, field_tiles
from ..price_observer import CROP_BY_NAME
from .base import Worker


@dataclass(frozen=True)
class CropWorker(Worker):
    fields: tuple
    plant_limit: int | None
    planting_crop: str | None

    def action(self, obs, position, inventory):
        tiles = field_tiles(obs["farms"][obs["player"]], self.fields)
        if any(inventory.get(crop, 0) for crop in CROP_BY_NAME):
            return self.move_or_act(position, SHED, ["DROP"])

        ripe = [
            field
            for field, tile in tiles.items()
            if isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") in CROP_BY_NAME
            and obs["day"] - tile["planted_day"]
            >= CROP_BY_NAME[tile["crop"]].harvest_day
        ]
        if ripe:
            return self.move_or_act(position, self.nearest(position, ripe), ["HARVEST"])

        thirsty = [
            field
            for field, tile in tiles.items()
            if isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") in CROP_BY_NAME
            and not tile["watered_today"]
        ]
        if thirsty:
            return self.move_or_act(
                position, self.nearest(position, thirsty), ["WATER"]
            )

        if self.planting_crop is None or self._limit_reached(obs, tiles):
            return ["PASS"]
        empty = [field for field, tile in tiles.items() if tile is None]
        seeds = obs["private"]["seeds"].get(self.planting_crop, 0)
        if empty and seeds:
            return self.move_or_act(
                position, self.nearest(position, empty), ["PLANT", self.planting_crop]
            )
        if not seeds:
            return ["PASS"]
        weeds = [
            field
            for field, tile in tiles.items()
            if isinstance(tile, dict) and tile.get("kind") == "WEED"
        ]
        return (
            self.move_or_act(position, self.nearest(position, weeds), ["DIG"])
            if weeds
            else ["PASS"]
        )

    def _limit_reached(self, obs, tiles):
        if self.plant_limit is None:
            return False
        planted = sum(
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile["planted_day"] == obs["day"]
            for tile in tiles.values()
        )
        return planted >= self.plant_limit
