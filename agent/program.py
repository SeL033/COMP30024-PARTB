# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Action
from referee.game.constants import PLACEMENT_TURNS
from .board import State
from .negamax import negamax_action

class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Cascade game events.
    """

    def __init__(self, color: PlayerColor, **referee: dict):
        self._color = color
        self._state = State()

    def action(self, **referee: dict) -> Action:
        if self._state.placement_count < PLACEMENT_TURNS:
            return self._state.legal_actions()[0]
        return negamax_action(self._state, time_limit=2.0)

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        self._state.apply(action)
