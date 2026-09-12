"""
Command classes shared by the player (driven by InputHandler through
CommandBindings) and by any autonomous entity (driven directly from its
own state's decision logic). Every Command only records intent on the
receiver -- move_direction, jump_requested -- which every
src.entities.Entity already exposes, so the same instance works for both
a human-controlled entity and an AI-controlled one (e.g. a monster's
state calling MOVE_LEFT.execute(monster, dt) itself instead of going
through CommandBindings). Turning that intent into an actual effect
(how fast it translates into vx, whether a jump is currently allowed,
which way the sprite should be flipped) is resolved every frame by the
receiving entity's own state, never by the Command itself.
"""

from gale.command import Command


class MoveLeftCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        receiver.move_direction = -1


class MoveRightCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        receiver.move_direction = 1


class StopMoveLeftCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        if receiver.move_direction < 0:
            receiver.move_direction = 0


class StopMoveRightCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        if receiver.move_direction > 0:
            receiver.move_direction = 0


class JumpCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        receiver.jump_requested = True
        receiver.jump_held = True


class StopJumpCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        receiver.jump_held = False


class DashCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        receiver.dash_requested = True


class AttackCommand(Command):
    def execute(self, receiver, dt: float = 0.0) -> None:
        receiver.attack_requested = True


MOVE_LEFT = MoveLeftCommand()
MOVE_RIGHT = MoveRightCommand()
STOP_MOVE_LEFT = StopMoveLeftCommand()
STOP_MOVE_RIGHT = StopMoveRightCommand()
JUMP = JumpCommand()
STOP_JUMP = StopJumpCommand()
DASH = DashCommand()
ATTACK = AttackCommand()
