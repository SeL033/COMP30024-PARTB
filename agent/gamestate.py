from referee.game import (
    PlayerColor, Coord, Direction,
    Action, PlaceAction, MoveAction, EatAction, CascadeAction,
    BOARD_N, CARDINAL_DIRECTIONS,
    Board, GamePhase,
    PLACEMENT_TURNS, INITIAL_STACK_HEIGHT, MAX_TURNS
)

class GameState:
    """
    This is used for board representation inside Minimax.
    Stores the board as a flat dict {Coord: (color_int, height)}.
    color_int: 0 = empty, 1 = RED, -1 = BLUE
    """
    __slots__ = (
        "_cells", "turn", "placement_count",
        "play_turns", "position_history"
    )

    COLOR_INT = {PlayerColor.RED: 1, PlayerColor.BLUE: -1}
    INT_COLOR = {1: PlayerColor.RED, -1: PlayerColor.BLUE}

    def __init__(self):
        self._cells: dict[Coord, tuple[int, int]] = {
            Coord(r, c): (0, 0)
            for r in range(BOARD_N) for c in range(BOARD_N)
        }
        self.turn: PlayerColor = PlayerColor.RED
        self.placement_count: int = 0
        self.play_turns: int = 0
        self.position_history: list[int] = []

    @classmethod
    def from_board(cls, board: Board) -> "GameState":
        """
        Sync from referee Board object.
        - iterate over all cells on the board
        - store each cell as (color_int, height) in self.cells
        """
        return

    def copy(self) -> "GameState":
        """
        Return a deep copy of this GameState.
        - copy all attributes
        """
        return

    @property
    def phase(self) -> GamePhase:
        return GamePhase.PLACEMENT if self.placement_count < PLACEMENT_TURNS else GamePhase.PLAY

    def get_color_int(self, color: PlayerColor) -> int:
        return self.COLOR_INT[color]

    def token_count(self, color_int: int) -> int:
        """Return total token count for the given color_int (1=RED, -1=BLUE)"""
        return

    def stack_coords(self, color_int: int) -> list[Coord]:
        """Return list of coords occupied by the given color_int."""
        return

    def board_hash(self) -> int:
        """Return a hash of the current board state + turn for threefold repetition detection."""
        return

    def is_terminal(self) -> bool:
        """
        Return True if the game is over.
        Check:
          1. Still in placement phase -> not terminal
          2. Either player has 0 tokens -> terminal
          3. Play turns >= MAX_TURNS -> terminal
          4. Threefold repetition -> terminal
          5. No legal actions -> terminal
        """
        return

    def winner(self) -> PlayerColor | None:
        """
        Return the winner, or None for draw.
        - if RED tokens == 0 -> BLUE wins
        - if BLUE tokens == 0 -> RED wins
        - else compare token counts, more = winner, equal = None (draw)
        """
        return

    def has_legal_actions(self) -> bool:
        """
        Return True if the current player has at least one legal action.
        """
        return

    def legal_actions(self) -> list[Action]:
        if self.phase == GamePhase.PLACEMENT:
            return self.legal_place_actions()
        return self.legal_play_actions()

    def legal_place_actions(self) -> list[Action]:
        """
        Return all legal PlaceActions for the current player.
          - can only place on empty cells
          - after the first placement, cannot place adjacent to any enemy stack
        """
        return

    def is_adjacent_to(self, coord: Coord, color_int: int) -> bool:
        """
        Return True if coord is adjacent (cardinal) to any cell of the given color_int.
        """
        return

    def legal_play_actions(self) -> list[Action]:
        """
        Return all legal actions (MOVE, EAT, CASCADE) for the current player.
        """
        return

    def apply_action(self, action: Action) -> "GameState":
        """
        Return a new GameState after applying the given action.
        - copy the current state
        - apply the action to the copy
        - flip the turn
        - if is in play phase, increment play_turns and record board hash
        """
        return

    def apply_place(self, action: PlaceAction):
        """
        Apply a PLACE action.
        - set the cell at action.coord to (my_color_int, INITIAL_STACK_HEIGHT)
        - increment placement_count
        """
        return

    def apply_move(self, action: MoveAction):
        """
        Apply a MOVE action.
        - if destination is empty: relocate stack
        - if destination is friendly: merge (sum heights)
        - clear source cell
        """
        return

    def apply_eat(self, action: EatAction):
        """
        Apply an EAT action.
        - move attacker to destination, replacing enemy stack
        - clear source cell
        """
        return

    def apply_cascade(self, action: CascadeAction):
        """
        Apply a CASCADE action.
        - remove source stack
        """
        return

    def push(self, curr_board: dict, coord: Coord, d: Direction) -> dict:
        """
        apply the attacker PUSH enemy action in CASCADE
        """
        return