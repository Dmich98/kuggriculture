from abc import ABC, abstractmethod


class Worker(ABC):
    @staticmethod
    def move_toward(position, target):
        x, y = position
        target_x, target_y = target
        if x != target_x:
            return ["EAST"] if x < target_x else ["WEST"]
        if y != target_y:
            return ["SOUTH"] if y < target_y else ["NORTH"]
        return ["PASS"]

    @staticmethod
    def nearest(position, targets):
        return min(
            targets,
            key=lambda target: (
                abs(position[0] - target[0]) + abs(position[1] - target[1])
            ),
        )

    @staticmethod
    def move_or_act(position, target, action):
        return action if position == target else Worker.move_toward(position, target)

    @abstractmethod
    def action(self, obs, position, inventory):
        """Return one game action."""
