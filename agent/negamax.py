import time
import math
from referee.game import PlayerColor
from .evaluate import evaluate, order_actions, high_value_actions
from .transposition import hash_state, TTEntry, EXACT, LOWER, UPPER

def _turn_color(state):
    # Return the PlayerColor of whichever player is currently to move
    return PlayerColor.RED if state.red_turn else PlayerColor.BLUE

def _terminal_value(state, color):
    # Return 1.0 if color wins, -1.0 if color loses, 0.0 for draw
    winner = state.winner()
    if winner is None:
        return 0.0
    return 1.0 if winner == color else -1.0

def _negamax(state, depth, alpha, beta, deadline, tt):
    # Negamax with alpha-beta pruning and transposition table lookup.
    # Returns the value of the position from the current player's perspective.
 
    # Time cutoff: return static evaluation immediately
    if time.time() >= deadline:
        return evaluate(state, _turn_color(state))
    
    # Terminal node: return exact outcome
    if state.game_finished():
        return _terminal_value(state, _turn_color(state))
    
    # Depth cutoff: run quiescence search instead of static eval
    # to avoid horizon effect on tactical positions
    if depth == 0:
        return _quiescence(state, alpha, beta, deadline)
    
    alpha_orig = alpha
    beta_orig = beta

    # Transposition table lookup: reuse a previously computed result if available
    h = hash_state(state)
    tt_entry = tt.get(h)
    tt_move = None
    if tt_entry is not None:
        tt_move = tt_entry.best_action
        if tt_entry.depth >= depth:
            if tt_entry.flag == EXACT:
                return tt_entry.value
            elif tt_entry.flag == LOWER and tt_entry.value > alpha:
                alpha = tt_entry.value
            elif tt_entry.flag == UPPER and tt_entry.value < beta:
                beta = tt_entry.value
            if alpha >= beta:
                return tt_entry.value

    actions = state.legal_actions()
    if not actions:
        return _terminal_value(state, _turn_color(state))
    
    # Order actions to improve alpha-beta pruning efficiency;
    # place the TT best move first if available
    my_color_int = 1 if state.red_turn else -1
    actions = order_actions(actions, state, my_color_int)
    if tt_move is not None and tt_move in actions:
        actions = [tt_move] + [a for a in actions if a != tt_move]
    
    best_value = -math.inf
    best_action = actions[0]
    for action in actions:
        if time.time() >= deadline:
            break
        state.apply(action)
        # Negamax: negate the child's value since it is from the opponent's perspective
        child_value = -_negamax(state, depth - 1, -beta, -alpha, deadline, tt)
        state.undo()
        if child_value > best_value:
            best_value = child_value
            best_action = action
        if child_value > alpha:
            alpha = child_value
        if alpha >= beta:
            # Beta cut-off: opponent will not allow this line
            break

    # Store result in transposition table with appropriate flag
    if best_value <= alpha_orig:
        flag = UPPER
    elif best_value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT
    tt[h] = TTEntry(depth, best_value, flag, best_action)

    return best_value

def _search_root(state, depth, deadline, ordered_actions, tt):
    # Search all root actions at a fixed depth; return (best_value, best_action, completed).
    # completed is False if the search was cut off by the deadline mid-way.
    alpha = -math.inf
    beta = math.inf
    best_value = -math.inf
    best_action = ordered_actions[0]
    for action in ordered_actions:
        if time.time() >= deadline:
            return best_value, best_action, False
        state.apply(action)
        child_value = -_negamax(state, depth - 1, -beta, -alpha, deadline, tt)
        state.undo()
        if child_value > best_value:
            best_value = child_value
            best_action = action
        if child_value > alpha:
            alpha = child_value
    return best_value, best_action, True

def _quiescence(state, alpha, beta, deadline):
    # Quiescence search: continue searching only high-value actions (EAT and profitable CASCADE)
    # beyond the depth cutoff to avoid evaluating positions mid-capture sequence.
    if time.time() >= deadline:
        return evaluate(state, _turn_color(state))
    
    if state.game_finished():
        return _terminal_value(state, _turn_color(state))
    
    # Stand-pat: the current player can always choose to make no capture
    stand_pat = evaluate(state, _turn_color(state))
    if stand_pat >= beta:
        return stand_pat
    if stand_pat > alpha:
        alpha = stand_pat
        
    my_color_int = 1 if state.red_turn else -1
    candidate_actions = high_value_actions(state, my_color_int)
    if not candidate_actions:
        return stand_pat
    
    candidate_actions = order_actions(candidate_actions, state, my_color_int)
    
    for action in candidate_actions:
        if time.time() >= deadline:
            break
        state.apply(action)
        value = -_quiescence(state, -beta, -alpha, deadline)
        state.undo()
        if value >= beta:
            return value
        if value > alpha:
            alpha = value
            
    return alpha

def negamax_action(state, time_limit=2.0):
    # Select the best action using iterative deepening negamax with alpha-beta pruning.
    # Returns the best action found within the time budget.
    actions = state.legal_actions()
    if not actions:
        raise RuntimeError("no legal actions")
    if len(actions) == 1:
        return actions[0]
    
    my_color_int = 1 if state.red_turn else -1
    actions = order_actions(actions, state, my_color_int)
    
    deadline = time.time() + time_limit
    best_action = actions[0]
    tt = {}
    
    depth = 1
    while time.time() < deadline:
        _, action, complete = _search_root(state, depth, deadline, actions, tt)
        if complete or depth == 1:
            best_action = action
            # Move best action to front for better ordering at next depth
            actions = [best_action] + [x for x in actions if x != best_action]
        depth += 1

    return best_action
    

