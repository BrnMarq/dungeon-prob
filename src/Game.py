import pygame

from gale.game import Game
from gale.input_handler import InputData, InputListener
from gale.state import StateMachine

import settings
from src.states.TitleState import TitleState
from src.states.PlayState import PlayState
from src.states.PauseState import PauseState
from src.states.GameOverState import GameOverState
from src.states.VictoryState import VictoryState


class DungeonProb(Game, InputListener):
    def init(self) -> None:
        self.state_machine = StateMachine({
            'title': TitleState,
            'play': PlayState,
            'pause': PauseState,
            'game_over': GameOverState,
            'victory': VictoryState,
        })
        self.state_machine.change('title')

    def update(self, dt: float) -> None:
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_machine.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if (input_id == 'quit' and input_data.pressed):
            self.quit()
        elif input_id == 'toggle_debug_hitboxes' and input_data.pressed:
            settings.DEBUG_HITBOXES = not settings.DEBUG_HITBOXES
        else:
            self.state_machine.on_input(input_id, input_data)
