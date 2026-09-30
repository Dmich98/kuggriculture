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


@dataclass(frozen=True)
class Product:
    name: str
    minimum_sell_price: int


@dataclass(frozen=True)
class AnimalPlan:
    animal: str
    product: str
    quantity: int
    purchase_cost: int
    first_yield_day: int
    yield_interval: int
    feed_per_day: int


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
FIELD_CROPS = tuple(crop for crop in CROPS if crop.name != "STRAWBERRY")
ANIMAL_PRODUCTS = (Product("EGG", 50), Product("MILK", 160))
MARKET_PRODUCTS = CROPS + ANIMAL_PRODUCTS
MARKET_PRODUCT_BY_NAME = {product.name: product for product in MARKET_PRODUCTS}
ANIMAL_PLANS = (
    AnimalPlan("GOOSE", "EGG", 2, 300, 4, 1, 1),
    AnimalPlan("COW", "MILK", 2, 400, 8, 2, 1),
)


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
            for product in MARKET_PRODUCTS:
                prices = self.prices_by_crop.setdefault(product.name, [])
                prices.append(obs["market"]["prices"].get(product.name, 0))
                del prices[: -self.history_size]
            self.last_day = day

    def is_high(self, product, price):
        prices = self.prices_by_crop.get(product.name, [])
        if len(prices) < 2:
            return price >= product.minimum_sell_price

        low, high = min(prices), max(prices)
        return (
            price >= product.minimum_sell_price and price >= high - (high - low) * 0.35
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


def recommend_animal(obs, excluded_animals=()):
    """Recommend a livestock batch only when it pays for itself this season."""

    remaining_days = 29 - obs["day"]
    wheat_price = obs["market"]["prices"].get("WHEAT", 0)
    candidates = []
    for plan in ANIMAL_PLANS:
        if plan.animal in excluded_animals:
            continue
        production_days = max(
            0, (remaining_days - plan.first_yield_day) // plan.yield_interval + 1
        )
        yield_units = max(0, production_days * 2 - 1)
        revenue = (
            obs["market"]["prices"].get(plan.product, 0) * yield_units * plan.quantity
        )
        feed_cost = wheat_price * plan.feed_per_day * remaining_days * plan.quantity
        worker_cost = remaining_days
        profit = revenue - feed_cost - plan.purchase_cost * plan.quantity - worker_cost
        if profit > 0:
            candidates.append((profit, plan))
    return (
        max(candidates, default=None, key=lambda candidate: candidate[0])[1]
        if candidates
        else None
    )
