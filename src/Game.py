import pygame

from gale.game import Game
from gale.input_handler import InputData, InputListener
from gale.save import SaveManager
from gale.state import StateMachine, StateStack

from src.states.TitleState import TitleState
from src.states.PlayState import PlayState
from src.states.GameOverState import GameOverState
from src.states.VictoryState import VictoryState
from src.states.PauseMenuState import PauseMenuState


class DungeonProb(Game, InputListener):
    def init(self) -> None:
        self.state_machine = StateMachine({
            'title': TitleState,
            'play': PlayState,
            'game_over': GameOverState,
            'victory': VictoryState,
        })
        self.state_machine.change('title')

        # The pause menu (src.states.PauseMenuState) - empty stack means
        # "not paused". Esc (on_input's "quit" branch below) pushes/pops
        # it; while non-empty, update() skips state_machine entirely
        # (freezing whichever screen is underneath) and render() draws
        # it on top of state_machine's own (frozen) frame.
        self.pause_stack = StateStack()
        self.save_manager = SaveManager()

    def update(self, dt: float) -> None:
        if self.pause_stack.states:
            self.pause_stack.update(dt)
            return
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_machine.render(surface)
        if self.pause_stack.states:
            self.pause_stack.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == 'quit' and input_data.pressed:
            if self.pause_stack.states:
                self.pause_stack.pop()
            else:
                self.pause_stack.push(PauseMenuState(self.pause_stack, self))
            return

        if self.pause_stack.states:
            self.pause_stack.on_input(input_id, input_data)
            return

        self.state_machine.on_input(input_id, input_data)
