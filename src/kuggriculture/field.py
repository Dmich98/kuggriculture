SHED = (4, 4)

# The complete game map. Planting and livestock use separate zones inside it.
GAME_FIELD = tuple((x, y) for y in range(10) for x in range(10))

# The complete 4 x 4 farm area, listed one vertical strip at a time.
FARM_FIELD = (
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (4, 1),
    (4, 2),
    (4, 3),
    (4, 4),
)

# Each farmer owns two vertical strips after the starter harvest.
SECOND_FARMER_ZONE = FARM_FIELD[:8]
MAIN_FARMER_ZONE = FARM_FIELD[8:]

LIVESTOCK_FIELD = (
    (0, 0),
    (1, 0),
    (2, 0),
    (3, 0),
    (4, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
)
LIVESTOCK_SITES = {
    "GOOSE": ((0, 4), (0, 3)),
    "COW": ((0, 1), (0, 2)),
}

# The purchased NE quadrant belongs to specialists.
BERRY_FIELD = (
    (5, 0),
    (6, 0),
    (7, 0),
    (5, 1),
    (6, 1),
    (7, 1),
)


def is_starter_phase(day):
    return day <= 3


def planting_limit(day):
    return 4 if is_starter_phase(day) else None


def total_planting_limit(day):
    return 4 if is_starter_phase(day) else len(FARM_FIELD)


def main_farmer_fields(day):
    return MAIN_FARMER_ZONE


def second_farmer_fields(day):
    return MAIN_FARMER_ZONE if is_starter_phase(day) else SECOND_FARMER_ZONE


def active_fields(day):
    return MAIN_FARMER_ZONE if is_starter_phase(day) else FARM_FIELD


def specialists_unlocked(farm):
    return "NE" in farm.get("unlocked_quadrants", ())


def field_tiles(farm, fields):
    return {field: farm["tiles"][field[1]][field[0]] for field in fields}
