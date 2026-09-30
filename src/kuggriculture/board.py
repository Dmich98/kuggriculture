def move_toward(current, target):
    x, y = current
    target_x, target_y = target

    if x < target_x:
        return ["EAST"]
    if x > target_x:
        return ["WEST"]
    if y < target_y:
        return ["SOUTH"]
    if y > target_y:
        return ["NORTH"]
    return ["PASS"]


def nearest(position, targets):
    return min(
        targets,
        key=lambda target: abs(position[0] - target[0]) + abs(position[1] - target[1]),
    )


def move_or_act(position, target, action):
    return action if position == target else move_toward(position, target)
