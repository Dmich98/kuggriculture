SHED = (4, 4)

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


def field_tiles(farm, fields):
    return {field: farm["tiles"][field[1]][field[0]] for field in fields}
