# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Action
from referee.game.constants import PLACEMENT_TURNS, MAX_TURNS
from .board import State
from .mcts import mcts_action
from .evaluate import placement_score

MAX_OUR_MOVES = 60
DEFAULT_TIME_BUDGET = 2.0
SAFETY_BUFFER_SEC = 5.0
MIN_TIME_PER_MOVE = 0.1
MAX_TIME_PER_MOVE = 5.0
MIN_MOVES_LEFT_GUESS = 20

class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Cascade game events.
    """

    def __init__(self, color: PlayerColor, **referee: dict):
        self._color = color
        self._state = State()
        self._mcts_root = None

    def action(self, **referee: dict) -> Action:
        time_rem = referee.get("time_remaining")
        if time_rem is None:
            budget = DEFAULT_TIME_BUDGET
        else:
            moves_left = max(MIN_MOVES_LEFT_GUESS, MAX_OUR_MOVES - self._state.playturn_count // 2)
            usable_time = time_rem - SAFETY_BUFFER_SEC
            budget = max(MIN_TIME_PER_MOVE, min(MAX_TIME_PER_MOVE, usable_time / moves_left))
        
        if self._state.placement_count < PLACEMENT_TURNS:
            actions = self._state.legal_actions()
            return max(actions, key=lambda action: placement_score(action.coord, self._state, self._color))
        action, self._mcts_root = mcts_action(self._state, time_limit=budget, root=self._mcts_root)
        return action

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        self._state.apply(action)
        if self._mcts_root is not None:
            child = next((c for c in self._mcts_root.children if c.action == action), None)
            self._mcts_root = child
            if self._mcts_root is not None:
                self._mcts_root.parent = None
