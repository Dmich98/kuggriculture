from dataclasses import dataclass, field


@dataclass(frozen=True)
class Crop:
    name: str
    seed_cost: int
    harvest_day: int
    expected_yield: int
    minimum_sell_price: int


@dataclass(frozen=True)
class Recommendation:
    crop: Crop
    price: int
    expected_profit: int
    profit_per_day: float


CROPS = (
    Crop(
        name="WHEAT",
        seed_cost=10,
        harvest_day=4,
        expected_yield=4,
        minimum_sell_price=25,
    ),
    Crop(
        name="CARROT",
        seed_cost=20,
        harvest_day=3,
        expected_yield=3,
        minimum_sell_price=35,
    ),
    Crop(
        name="TOMATO",
        seed_cost=50,
        harvest_day=8,
        expected_yield=4,
        minimum_sell_price=60,
    ),
    Crop(
        name="STRAWBERRY",
        seed_cost=100,
        harvest_day=10,
        expected_yield=4,
        minimum_sell_price=120,
    ),
)

CROP_BY_NAME = {crop.name: crop for crop in CROPS}


@dataclass
class PriceObserver:
    """Keeps one price snapshot per day for each crop."""

    history_size: int = 6
    prices_by_crop: dict[str, list[int]] = field(default_factory=dict)
    last_day: int | None = None

    def observe(self, obs):
        day = obs["day"]
        if self.last_day is not None and day < self.last_day:
            self.prices_by_crop.clear()

        if day != self.last_day:
            for crop in CROPS:
                prices = self.prices_by_crop.setdefault(crop.name, [])
                prices.append(obs["market"]["prices"].get(crop.name, 0))
                del prices[:-self.history_size]
            self.last_day = day

    def is_high(self, crop, price):
        prices = self.prices_by_crop.get(crop.name, [])
        if len(prices) < 2:
            return price >= crop.minimum_sell_price

        low, high = min(prices), max(prices)
        return (
            price >= crop.minimum_sell_price
            and price >= high - (high - low) * 0.35
        )


price_observer = PriceObserver()


def can_harvest_this_season(crop, day):
    return day + crop.harvest_day <= 29


def evaluate(crop, price):
    expected_profit = price * crop.expected_yield - crop.seed_cost
    return Recommendation(
        crop=crop,
        price=price,
        expected_profit=expected_profit,
        profit_per_day=expected_profit / crop.harvest_day,
    )


def recommend(obs, crops=CROPS):
    day = obs["day"]
    prices = obs["market"]["prices"]
    candidates = [
        evaluate(crop, prices.get(crop.name, 0))
        for crop in crops
        if can_harvest_this_season(crop, day)
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate.profit_per_day)


def seed_order(obs, quantity, crops=CROPS):
    recommendation = recommend(obs, crops)
    if recommendation is None:
        return None

    return ["BUY_SEED", recommendation.crop.name, quantity]
