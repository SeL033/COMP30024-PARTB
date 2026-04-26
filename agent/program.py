# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part B: Game Playing Agent

import math
import time

from referee.game import PlayerColor, Coord, Direction, \
    Action, PlaceAction, MoveAction, EatAction, CascadeAction, \
        Board, GamePhase, PLACEMENT_TURNS, INITIAL_STACK_HEIGHT, \
            MAX_TURNS, BOARD_N, CARDINAL_DIRECTIONS
from gamestate import GameState

CENTER_COOR = 3.5  # center of 8x8 board
  
class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Cascade game events.
    """

    def __init__(self, color: PlayerColor, **referee: dict):
        """
        This constructor method runs when the referee instantiates the agent.
        Any setup and/or precomputation should be done here.
        """
        self._color = color
        self._turn_count = 0
        self._board = Board()
        self._gs = GameState()
        
        time_rem = referee.get("time_remaining")
        self._time_per_move = 2.5 if time_rem is None else min(2.5, time_rem / 40)
        
        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as RED (first player)")
            case PlayerColor.BLUE:
                print("Testing: I am playing as BLUE")

    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object.
        """
        time_rem = referee.get("time_remaining")
        if time_rem is not None:
            turns_left = max(1, 150 - self._turn_count)
            self._time_per_move = min(3.0, (time_rem - 5.0) / turns_left)
            self._time_per_move = max(0.1, self._time_per_move)
 
        if self._gs.phase == GamePhase.PLACEMENT:
            return self._placement_action()
        else:
            return minimax_action(
                self._gs, self._color,
                time_limit=self._time_per_move,
            )
            
        # Below we have hardcoded actions to be played depending on whether
        # the agent is playing as BLUE or RED. Obviously this won't work beyond
        # the initial moves of the game, so you should use some game playing
        # technique(s) to determine the best action to take.

        # # During placement phase (first 8 turns total, 4 per player)
        # if self._turn_count < 4:
        #     match self._color:
        #         case PlayerColor.RED:
        #             print("Testing: RED is playing a PLACE action")
        #             return PlaceAction(Coord(0, self._turn_count))
        #         case PlayerColor.BLUE:
        #             print("Testing: BLUE is playing a PLACE action")
        #             return PlaceAction(Coord(7, self._turn_count))

        # # During play phase
        # match self._color:
        #     case PlayerColor.RED:
        #         print("Testing: RED is playing a MOVE action")
        #         return MoveAction(Coord(0, 0), Direction.Down)
        #     case PlayerColor.BLUE:
        #         print("Testing: BLUE is playing a MOVE action")
        #         return MoveAction(Coord(7, 0), Direction.Up)

    def _placement_action(self) -> PlaceAction:
        """Greedy heuristic: pick the highest-scoring legal placement."""
        candidates = self._gs._legal_place_actions()
        return max(candidates,
                   key=lambda a: placement_score(a.coord, self._gs, self._color))
        
    def update(self, color: PlayerColor, action: Action, **referee: dict):
        """
        This method is called by the referee after a player has taken their
        turn. You should use it to update the agent's internal game state.
        """
        self._board.apply_action(action)
        self._gs = GameState.from_board(self._board)
        
        if color == self._color:
            self._turn_count += 1

        # There are four possible action types: PLACE, MOVE, EAT, and CASCADE.
        # Below we check which type of action was played and print out the
        # details of the action for demonstration purposes. You should replace
        # this with your own logic to update your agent's internal game state.
        match action:
            case PlaceAction(coord):
                print(f"Testing: {color} played PLACE action at {coord}")
            case MoveAction(coord, direction):
                print(f"Testing: {color} played MOVE action:")
                print(f"  Coord: {coord}")
                print(f"  Direction: {direction}")
            case EatAction(coord, direction):
                print(f"Testing: {color} played EAT action:")
                print(f"  Coord: {coord}")
                print(f"  Direction: {direction}")
            case CascadeAction(coord, direction):
                print(f"Testing: {color} played CASCADE action:")
                print(f"  Coord: {coord}")
                print(f"  Direction: {direction}")
            case _:
                raise ValueError(f"Unknown action type: {action}")

#
# Evaluation
#

def dist_to_center(coord: Coord) -> float:
    return abs(coord.r - CENTER_COOR) + abs(coord.c - CENTER_COOR)
 
def simulate_cascade(cells: dict, src: Coord, d: Direction, player: int
                      ) -> tuple[int, int]:
    """
    Simulate a cascade from src in direction d for player.
    Returns (enemy_tokens_lost, own_tokens_lost).
    Track net gain for both sides.
    """
    player_src, height = cells[src]
    if player_src != player or height < 2:
        return 0, 0
 
    curr_board = dict(cells)
    curr_board[src] = (0, 0)
 
    def push(board, coord, direction):
        cell = board[coord]
        if cell[0] == 0:
            return board
        dr = coord.r + direction.r
        dc = coord.c + direction.c
        if not (0 <= dr < BOARD_N and 0 <= dc < BOARD_N):
            board[coord] = (0, 0)
            return board
        dest = Coord(dr, dc)
        if board[dest][0] != 0:
            board = push(board, dest, direction)
        board[dest] = cell
        board[coord] = (0, 0)
        return board
 
    for i in range(1, height + 1):
        target_r = src.r + d.r * i
        target_c = src.c + d.c * i
        if not (0 <= target_r < BOARD_N and 0 <= target_c < BOARD_N):
            continue
        target_coord = Coord(target_r, target_c)
        if curr_board[target_coord][0] != 0:
            curr_board = push(curr_board, target_coord, d)
        curr_board[target_coord] = (player, 1)
 
    # Compare total tokens before vs after to find what was pushed off board.
    opp = -player
    old_opp_total = sum(h for color, h in cells.values() if color == opp)
    old_own_total = sum(h for color, h in cells.values() if color == player)
    new_opp_total = sum(h for color, h in curr_board.values() if color == opp)
    new_own_total = sum(h for color, h in curr_board.values() if color == player)

    enemy_lost = old_opp_total - new_opp_total
    own_lost   = old_own_total - new_own_total
    return max(0, enemy_lost), max(0, own_lost)

def _tactical_score(gs: GameState, my_color: int) -> float:
    """
    Compute score: 
    immediate EAT threats + non-suicidal CASCADE gains
    vs 
    opponent's threats against us.
    """
    opp_color = -my_color
    cells = gs._cells
 
    # EAT opportunities
    my_eat_gain = 0
    opp_eat_threat = 0
    for coord, (color, h) in cells.items():
        for d in CARDINAL_DIRECTIONS:
            dr, dc = coord.r + d.r, coord.c + d.c
            if not (0 <= dr < BOARD_N and 0 <= dc < BOARD_N):
                continue
            dest = Coord(dr, dc)
            dest_color, dest_h = cells[dest]
            if color == my_color and dest_color == opp_color and h >= dest_h:
                my_eat_gain += dest_h
            if color == opp_color and dest_color == my_color and h >= dest_h:
                opp_eat_threat += dest_h
 
    # Best CASCADE net gain
    my_best_cascade = 0
    opp_best_cascade = 0
    for coord, (color, h) in cells.items():
        if h < 2:
            continue
        if color == my_color:
            for d in CARDINAL_DIRECTIONS:
                e_lost, o_lost = simulate_cascade(cells, coord, d, my_color)
                net = e_lost - o_lost
                my_best_cascade = max(my_best_cascade, net)
        elif color == opp_color:
            for d in CARDINAL_DIRECTIONS:
                e_lost, o_lost = simulate_cascade(cells, coord, d, opp_color)
                net = e_lost - o_lost
                opp_best_cascade = max(opp_best_cascade, net)
 
    total = gs.token_count(my_color) + gs.token_count(opp_color)
    if total == 0:
        return 0.0
 
    tactical = (my_eat_gain + my_best_cascade - opp_eat_threat - opp_best_cascade) / max(total, 1)
    return max(-1.0, min(1.0, tactical))
 
 
def evaluate(gs: GameState, color: PlayerColor) -> float:
    """
    Heuristic evaluation scoring
    Returns a value in [-1, 1].
    """
    my_color = GameState.COLOR_INT[color]
    opp_color = -my_color
 
    my_tokens = gs.token_count(my_color)
    opp_tokens = gs.token_count(opp_color)
 
    if opp_tokens == 0 and gs.phase == GamePhase.PLAY:
        return 1.0
    if my_tokens == 0 and gs.phase == GamePhase.PLAY:
        return -1.0
 
    total = my_tokens + opp_tokens
    if total == 0:
        return 0.0
 
    # Token advantage
    token_adv = (my_tokens - opp_tokens) / total
 
    my_stacks = [(c, h) for c, (ci, h) in gs._cells.items() if ci == my_color]
    opp_stacks = [(c, h) for c, (ci, h) in gs._cells.items() if ci == opp_color]
    
    # Stack height average
    my_avg_h = (sum(h for _, h in my_stacks) / len(my_stacks)) if my_stacks else 0
    opp_avg_h = (sum(h for _, h in opp_stacks) / len(opp_stacks)) if opp_stacks else 0
    height_adv = (my_avg_h - opp_avg_h) / max(my_avg_h + opp_avg_h, 1)
 
    # Centrality
    my_center = sum(dist_to_center(c) for c, _ in my_stacks) / max(len(my_stacks), 1)
    opp_center = sum(dist_to_center(c) for c, _ in opp_stacks) / max(len(opp_stacks), 1)
    center_adv = (opp_center - my_center) / 7.0
 
    # Mobility
    my_actions = len(gs.legal_play_actions()) if gs.phase == GamePhase.PLAY else 0
    opp_actions = 0
    for coord, (ci, h) in gs._cells.items():
        if ci != opp_color:
            continue
        for d in CARDINAL_DIRECTIONS:
            dr, dc = coord.r + d.r, coord.c + d.c
            if not (0 <= dr < BOARD_N and 0 <= dc < BOARD_N):
                continue
            dest_ci, dest_h = gs._cells[Coord(dr, dc)]
            if dest_ci == 0 or dest_ci == opp_color:
                opp_actions += 1
            if dest_ci == my_color and h >= dest_h:
                opp_actions += 1
        if h >= 2:
            opp_actions += 4
    mobility_adv = (my_actions - opp_actions) / max(my_actions + opp_actions, 1)
 
    # Tactical
    tactical = _tactical_score(gs, my_color)
 
    return (
        0.25 * token_adv +
        0.30 * tactical +
        0.12 * height_adv +
        0.20 * center_adv +
        0.13 * mobility_adv
    )
 
 
def placement_score(coord: Coord, gs: GameState, color: PlayerColor) -> float:
    """
    Score a placement coordinate during the placement phase.
 
    Expressed as ratios in [0, 1]
    - 0.5 = equal, >0.5 = advantage.
 
    Components:
      - centrality_ratio  : my avg centrality vs opp (lower dist = better)
      - spacing_ratio     : my avg inter-stack spacing vs opp (target = 2)
      - safety_ratio      : exposure penalty — opp immediate CASCADE threat vs mine
 
    The first placement (empty board) uses only centrality.
    Spacing is only meaningful once each side has >= 2 stacks.
    Safety is only meaningful once first player has placed a stack.
    """
    my_color = GameState.COLOR_INT[color]
    opp_color = -my_color
    is_second = (color == PlayerColor.BLUE)
 
    # Simulate placing at coord
    my_coords = [c for c, (ci, h) in gs._cells.items() if ci == my_color] + [coord]
    opp_coords = [c for c, (ci, h) in gs._cells.items() if ci == opp_color]
 
    # Centrality
    my_center_dist = sum(dist_to_center(c) for c in my_coords) / len(my_coords)
    if opp_coords:
        opp_center_dist = sum(dist_to_center(c) for c in opp_coords) / len(opp_coords)
    else:
        # No opp stacks yet: score purely on absolute centrality
        opp_center_dist = 7.0

    centrality_ratio = opp_center_dist / (my_center_dist + opp_center_dist + 1e-9)
 
    # Spacing
    # Target inter-stack spacing of 2 manhattan
    spacing_ratio = 0.5
    if len(my_coords) >= 2 and len(opp_coords) >= 2:
        def _avg_spacing(coords):
            if len(coords) < 2:
                return 2.0
            total = sum(
                abs(coords[i].r - coords[j].r) + abs(coords[i].c - coords[j].c)
                for i in range(len(coords))
                for j in range(i + 1, len(coords))
            )
            pairs = len(coords) * (len(coords) - 1) / 2
            return total / pairs
 
        my_spacing = _avg_spacing(my_coords)
        opp_spacing = _avg_spacing(opp_coords)
 
        # Score how close each side's spacing is to the target of 2
        my_spacing_score  = 1.0 / (1.0 + abs(my_spacing  - 2.0))
        opp_spacing_score = 1.0 / (1.0 + abs(opp_spacing - 2.0))
        spacing_ratio = my_spacing_score / (my_spacing_score + opp_spacing_score + 1e-9)
 
    # Safety
    # Compare best net cascade gain for each side.
    cascade_ratio = 0.5
 
    if opp_coords:
    # only meaningful once the opponent has at least one stack
        temp_cells = dict(gs._cells)
        temp_cells[coord] = (my_color, INITIAL_STACK_HEIGHT)
 
        my_best = 0
        for c in my_coords:
            for d in CARDINAL_DIRECTIONS:
                e_lost, o_lost = simulate_cascade(temp_cells, c, d, my_color)
                net = e_lost - o_lost
                if net > my_best:
                    my_best = net
 
        opp_best = 0
        for c in opp_coords:
            for d in CARDINAL_DIRECTIONS:
                e_lost, o_lost = simulate_cascade(temp_cells, c, d, opp_color)
                net = e_lost - o_lost
                if net > opp_best:
                    opp_best = net
 
        cascade_ratio = (my_best + 1e-9) / (my_best + opp_best + 1e-9)
 
    # Weighted combination
    if is_second:
        w_centrality = 0.40
        w_spacing    = 0.15
        w_cascade    = 0.45
    else:
        w_centrality = 0.45
        w_spacing    = 0.20
        w_cascade    = 0.40
 
    return (
        w_centrality * centrality_ratio +
        w_spacing    * spacing_ratio    +
        w_cascade    * cascade_ratio
    )
 
def action_priority(action: Action, gs: GameState, my_color: int) -> float:
    """
    Score an action for move ordering in alpha-beta.
    """
    if isinstance(action, EatAction):
        dest_r = action.coord.r + action.direction.r
        dest_c = action.coord.c + action.direction.c
        if 0 <= dest_r < BOARD_N and 0 <= dest_c < BOARD_N:
            _, dest_h = gs._cells[Coord(dest_r, dest_c)]
            return 10 + dest_h
 
    if isinstance(action, CascadeAction):
        e_lost, o_lost = simulate_cascade(gs._cells, action.coord, action.direction, my_color)
        net = e_lost - o_lost
        if net > 0:
            return 10 + net
        return net  # suicidal cascade last
 
    if isinstance(action, MoveAction):
        return 1
 
    return 0
 
def order_actions(actions: list[Action], gs: GameState, my_color: int) -> list[Action]:
    """Sort actions by priority descending for better alpha-beta pruning."""
    return sorted(actions, key=lambda a: action_priority(a, gs, my_color), reverse=True)

#
#  Minimax + Alpha-Beta
#

def _minimax(
    gs: GameState,
    my_color: PlayerColor,
    depth: int,
    alpha: float,
    beta: float,
    deadline: float,
) -> float:
    """
    Minimax with alpha-beta pruning.
    Returns evaluation score from my_color's perspective in [-1, 1].
    my_color is the maximiser.
    """
    # Time check
    if time.time() >= deadline:
        return evaluate(gs, my_color)
 
    # Terminal state
    if gs.is_terminal():
        w = gs.winner()
        if w == my_color:
            return 1.0
        elif w is None:
            return 0.0
        else:
            return -1.0
 
    # Depth cutoff
    if depth == 0:
        return evaluate(gs, my_color)
 
    my_ci = GameState.COLOR_INT[my_color]
    is_maximising = (gs.turn == my_color)
    actions = order_actions(gs.legal_play_actions(), gs, my_ci)
 
    if not actions:
        return evaluate(gs, my_color)
 
    if is_maximising:
        value = -math.inf
        for action in actions:
            if time.time() >= deadline:
                break
            child = gs.apply_action(action)
            value = max(value, _minimax(child, my_color, depth - 1, alpha, beta, deadline))
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # beta cut-off
        return value
    else:
        value = math.inf
        for action in actions:
            if time.time() >= deadline:
                break
            child = gs.apply_action(action)
            value = min(value, _minimax(child, my_color, depth - 1, alpha, beta, deadline))
            beta = min(beta, value)
            if beta <= alpha:
                break  # alpha cut-off
        return value
 
 
def minimax_action(
    gs: GameState,
    my_color: PlayerColor,
    time_limit: float = 1.2,
) -> Action:
    """
    Choose the best action using iterative deepening minimax with alpha-beta.
    Searches deeper and deeper until time runs out, always keeping the best
    action from the last fully completed depth.
    """
    actions = gs.legal_play_actions()
 
    if not actions:
        raise RuntimeError("No legal actions available")
    if len(actions) == 1:
        return actions[0]
 
    my_clr = GameState.COLOR_INT[my_color]
    actions = order_actions(actions, gs, my_clr)
 
    best_action = actions[0]
    deadline = time.time() + time_limit
 
    depth = 1
    while True:
        if time.time() >= deadline:
            break
        depth += 1
 
        depth_best_action = actions[0]
        depth_best_score = -math.inf
        alpha = -math.inf
        beta = math.inf
 
        for action in actions:
            if time.time() >= deadline:
                break
            child = gs.apply_action(action)
            score = _minimax(child, my_color, depth - 1, alpha, beta, deadline)
            if score > depth_best_score:
                depth_best_score = score
                depth_best_action = action
            alpha = max(alpha, depth_best_score)
 
            # Exit if found a winning move
            if depth_best_score >= 1.0:
                break

        if time.time() < deadline or depth == 1:
            best_action = depth_best_action
            actions = [best_action] + [a for a in actions if a != best_action]

    return best_action