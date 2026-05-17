from referee.game import PlayerColor, Direction, Coord, EatAction, MoveAction, CascadeAction
from referee.game.constants import BOARD_N, INITIAL_STACK_HEIGHT, PLACEMENT_TURNS
from .board import CENTRE

# weights (used for tuning)
W_TOKEN_ADV = 0.35
W_TACTICAL = 0.30
W_HEIGHT = 0.05
W_CENTER = 0.20
W_MOBILITY = 0.10

# (placement weights)
W_PLACE_CENTRALITY_FIRST = 0.40
W_PLACE_SPACING_FIRST = 0.20
W_PLACE_CASCADE_FIRST = 0.40
W_PLACE_CENTRALITY_SECOND = 0.40
W_PLACE_SPACING_SECOND = 0.15
W_PLACE_CASCADE_SECOND = 0.45

# constants
CENTER_COORD = 3.5
EPS = 1e-9
CARDINAL_DIRS = (Direction.Up, Direction.Down, Direction.Left, Direction.Right)

def _dist_to_center_index(index):
    return abs(index // BOARD_N - CENTER_COORD) + abs(index % BOARD_N - CENTER_COORD)

def simulate_cascade(state, src_index, direction, player_color_int):
    src_byte = state.board[src_index]
    src_color_int = 1 if src_byte > CENTRE else (-1 if src_byte < CENTRE else 0)
    if src_color_int != player_color_int:
        return 0, 0
    cascade_len = abs(src_byte - CENTRE)
    if cascade_len < 2:
        return 0, 0
    work = bytearray(state.board)
    increment = direction.r * BOARD_N + direction.c
    row = src_index // BOARD_N
    dir_c = direction.c
    work[src_index] = CENTRE
    own_lost = 0
    enemy_lost = 0
    placed_byte = CENTRE + 1 if player_color_int == 1 else CENTRE - 1
    
    for i in range(1, cascade_len + 1):
        next_index = src_index + increment * i
        if not (0 <= next_index < BOARD_N * BOARD_N):
            own_lost += cascade_len - (i - 1)
            break
        if dir_c != 0 and next_index // BOARD_N != row:
            own_lost += cascade_len - (i - 1)
            break
        
        if work[next_index] != CENTRE:
            attacker_loss, defender_loss = _push(work, next_index, increment, row, dir_c, player_color_int)
            own_lost += attacker_loss
            enemy_lost += defender_loss

        work[next_index] = placed_byte
        
    return enemy_lost, own_lost

def _push(work, index, increment, row, dir_c, attacker_color_int):
    cell = work[index]
    cell_height = abs(cell - CENTRE)
    cell_color_int = 1 if cell > CENTRE else -1
    next_index = index + increment
    
    off_board = (not (0 <= next_index < BOARD_N * BOARD_N) or (dir_c != 0 and next_index // BOARD_N != row))
    if off_board:
        work[index] = CENTRE
        if cell_color_int == attacker_color_int:
            return cell_height, 0
        else:
            return 0, cell_height
        
    attacker_loss = 0
    defender_loss = 0
    if work[next_index] != CENTRE:
        rec_attacker_loss, rec_defender_loss = _push(work, next_index, increment, row, dir_c, attacker_color_int)
        attacker_loss += rec_attacker_loss
        defender_loss += rec_defender_loss
    
    work[next_index] = cell
    work[index] = CENTRE
    return attacker_loss, defender_loss

def _estimate_mobility(state, color_int):
    count = 0
    for index in range(BOARD_N * BOARD_N):
        cell_byte = state.board[index]
        if cell_byte == CENTRE: continue
        if (cell_byte > CENTRE) != (color_int == 1): continue
        stack_height = cell_byte - CENTRE if color_int == 1 else CENTRE - cell_byte
        row, col = index // BOARD_N, index % BOARD_N
        for direction in CARDINAL_DIRS:
            adjacent_row, adjacent_col = row + direction.r, col + direction.c
            if not (0 <= adjacent_row < BOARD_N and 0 <= adjacent_col < BOARD_N): continue
            dest_byte = state.board[adjacent_row * BOARD_N + adjacent_col]
            if dest_byte == CENTRE:
                count += 1
                continue
            dest_color_int = 1 if dest_byte > CENTRE else -1
            dest_height   = dest_byte - CENTRE if dest_color_int == 1 else CENTRE - dest_byte
            if dest_color_int == color_int:
                count += 1
            elif stack_height >= dest_height:
                count += 1
        if stack_height >= 2:
            count += 4
    return count

def _tactical_score(state, my_color_int):
    opp_color_int = -my_color_int
    
    my_eat_gain = 0
    opp_eat_threat = 0
    my_best_cascade = 0
    opp_best_cascade = 0
    
    for index in range(BOARD_N * BOARD_N):
        cell_byte = state.board[index]
        if cell_byte == CENTRE: continue
        cell_color_int = 1 if cell_byte > CENTRE else -1
        stack_height = cell_byte - CENTRE if cell_color_int == 1 else CENTRE - cell_byte
        row, col = index // BOARD_N, index % BOARD_N
        
        for direction in CARDINAL_DIRS:
            adjacent_row = row + direction.r
            adjacent_col = col + direction.c
            if not (0 <= adjacent_row < BOARD_N and 0 <= adjacent_col < BOARD_N): continue
            dest_byte = state.board[adjacent_row * BOARD_N + adjacent_col]
            if dest_byte == CENTRE: continue
            dest_color_int = 1 if dest_byte > CENTRE else -1
            dest_height = dest_byte - CENTRE if dest_color_int == 1 else CENTRE - dest_byte
            if cell_color_int == my_color_int and dest_color_int == opp_color_int and stack_height >= dest_height:
                my_eat_gain += dest_height
            elif cell_color_int == opp_color_int and dest_color_int == my_color_int and stack_height >= dest_height:
                opp_eat_threat += dest_height
                
        if stack_height < 2: continue
        for direction in CARDINAL_DIRS:
            enemy_lost, own_lost = simulate_cascade(state, index, direction, cell_color_int)
            net = enemy_lost - own_lost
            if cell_color_int == my_color_int:
                if net > my_best_cascade:
                    my_best_cascade = net
            elif net > opp_best_cascade:
                opp_best_cascade = net 
    
    total_tokens = state.red_tokens + state.blue_tokens
    if total_tokens == 0:
        return 0.0
    
    tactical = (my_eat_gain + my_best_cascade - opp_eat_threat - opp_best_cascade) / max(total_tokens, 1)
    if tactical >  1.0: return  1.0
    if tactical < -1.0: return -1.0
    return tactical


def evaluate(state, color):
    my_color_int = 1 if color == PlayerColor.RED else -1
    opp_color_int = -my_color_int
    
    if my_color_int == 1:
        my_tokens, opp_tokens = state.red_tokens, state.blue_tokens
        my_stacks_count, opp_stacks_count = state.red_stacks, state.blue_stacks
    else:
        my_tokens, opp_tokens = state.blue_tokens, state.red_tokens
        my_stacks_count, opp_stacks_count = state.blue_stacks, state.red_stacks
        
    in_play = state.placement_count >= PLACEMENT_TURNS
    if in_play and opp_tokens == 0: return  1.0
    if in_play and my_tokens == 0:  return -1.0
    
    total = my_tokens + opp_tokens
    if total == 0: return 0.0
    
    token_adv = (my_tokens - opp_tokens) / total
    
    my_height_sum = 0
    opp_height_sum = 0
    my_center_sum = 0.0
    opp_center_sum = 0.0
    for index in range(BOARD_N * BOARD_N):
        cell_byte = state.board[index]
        if cell_byte == CENTRE: continue
        cell_color_int = 1 if cell_byte > CENTRE else -1
        stack_height = cell_byte - CENTRE if cell_color_int == 1 else CENTRE - cell_byte
        dist = _dist_to_center_index(index)
        if cell_color_int == my_color_int:
            my_height_sum += stack_height
            my_center_sum += dist
        else:
            opp_height_sum += stack_height
            opp_center_sum += dist
            
    my_avg_h = (my_height_sum / my_stacks_count) if my_stacks_count > 0 else 0.0
    opp_avg_h = (opp_height_sum / opp_stacks_count) if opp_stacks_count > 0 else 0.0
    height_adv = (my_avg_h - opp_avg_h) / max(my_avg_h + opp_avg_h, 1)
    
    my_center = my_center_sum / max(my_stacks_count, 1)
    opp_center = opp_center_sum / max(opp_stacks_count, 1)
    center_adv = (opp_center - my_center) / 7.0
    
    if in_play:
        my_actions = _estimate_mobility(state, my_color_int)
        opp_actions = _estimate_mobility(state, opp_color_int)
    else:
        my_actions = 0
        opp_actions = 0
    mobility_adv = (my_actions - opp_actions) / max(my_actions + opp_actions, 1)
    
    tactical = _tactical_score(state, my_color_int)
    
    return (
        W_TOKEN_ADV * token_adv +
        W_TACTICAL * tactical +
        W_HEIGHT * height_adv +
        W_CENTER * center_adv +
        W_MOBILITY * mobility_adv)

def action_priority(action, state, my_color_int):
    if isinstance(action, EatAction):
        dest_row = action.coord.r + action.direction.r
        dest_col = action.coord.c + action.direction.c
        if 0 <= dest_row < BOARD_N and 0 <= dest_col < BOARD_N:
            dest_byte = state.board[dest_row * BOARD_N + dest_col]
            dest_height = abs(dest_byte - CENTRE)
            return 10 + dest_height
        return 0
    
    if isinstance(action, CascadeAction):
        src_index = action.coord.r * BOARD_N + action.coord.c
        enemy_lost, own_lost = simulate_cascade(state, src_index, action.direction, my_color_int)
        net = enemy_lost - own_lost
        if net > 3:
            return 10 + net
        elif net > 0:
            return 5 + net
        else:
            return net
        
    if isinstance(action, MoveAction):
        return 1
    return 0

def order_actions(actions, state, my_color_int):
    return sorted(actions, key=lambda action: action_priority(action, state, my_color_int), reverse=True)


def placement_score(coord, state, color):
    my_color_int = 1 if color == PlayerColor.RED else -1
    opp_color_int = -my_color_int
    is_second = (color == PlayerColor.BLUE)
    
    my_coords = []
    opp_coords = []
    for index in range(BOARD_N * BOARD_N):
        cell_byte = state.board[index]
        if cell_byte == CENTRE: continue
        cell_coord = Coord(index // BOARD_N, index % BOARD_N)
        if (cell_byte > CENTRE) == (my_color_int == 1):
            my_coords.append(cell_coord)
        else:
            opp_coords.append(cell_coord)
            
    my_coords_after = my_coords + [coord]
    
    my_center_dist = sum(_dist_to_center_index(c.r * BOARD_N + c.c) for c in my_coords_after) / len(my_coords_after)
    if opp_coords:
        opp_center_dist = sum(_dist_to_center_index(c.r * BOARD_N + c.c) for c in opp_coords) / len(opp_coords)
    else:
        opp_center_dist = 7.0
    centrality_ratio = opp_center_dist / (my_center_dist + opp_center_dist + EPS)
    
    spacing_ratio = 0.5
    if len(my_coords_after) >= 2 and len(opp_coords) >= 2:
        def _avg_spacing(coords):
            total = 0
            for i in range(len(coords)):
                for j in range(i + 1, len(coords)):
                    total += abs(coords[i].r - coords[j].r) + abs(coords[i].c - coords[j].c)
            pairs = len(coords) * (len(coords) - 1) / 2
            return total / pairs if pairs > 0 else 2.0
            
        my_spacing = _avg_spacing(my_coords_after)
        opp_spacing = _avg_spacing(opp_coords)
        my_spacing_score = 1.0 / (1.0 + abs(my_spacing - 2.0))
        opp_spacing_score = 1.0 / (1.0 + abs(opp_spacing - 2.0))
        spacing_ratio = my_spacing_score / (my_spacing_score + opp_spacing_score + EPS)
        
    cascade_ratio = 0.5
    if opp_coords:
        temp_state = state.clone()
        place_idx = coord.r * BOARD_N + coord.c
        delta = INITIAL_STACK_HEIGHT if my_color_int == 1 else -INITIAL_STACK_HEIGHT
        temp_state.board[place_idx] = CENTRE + delta
        
        my_best = 0
        for c in my_coords_after:
            src_idx = c.r * BOARD_N + c.c
            for direction in CARDINAL_DIRS:
                enemy_lost, own_lost = simulate_cascade(temp_state, src_idx, direction, my_color_int)
                net = enemy_lost - own_lost
                if net > my_best:
                    my_best = net
                    
        opp_best = 0
        for c in opp_coords:
            src_idx = c.r * BOARD_N + c.c
            for direction in CARDINAL_DIRS:
                enemy_lost, own_lost = simulate_cascade(temp_state, src_idx, direction, opp_color_int)
                net = enemy_lost - own_lost
                if net > opp_best:
                    opp_best = net
        
        cascade_ratio = (my_best + EPS) / (my_best + opp_best + EPS)
        
    if is_second:
        w_centrality = W_PLACE_CENTRALITY_SECOND
        w_spacing = W_PLACE_SPACING_SECOND
        w_cascade = W_PLACE_CASCADE_SECOND
    else:
        w_centrality = W_PLACE_CENTRALITY_FIRST
        w_spacing = W_PLACE_SPACING_FIRST
        w_cascade = W_PLACE_CASCADE_FIRST
        
    return (
        w_centrality * centrality_ratio + 
        w_spacing * spacing_ratio +
        w_cascade * cascade_ratio)

def high_value_actions(state, my_color_int):
    result = []
    for action in state.legal_actions():
        if isinstance(action, EatAction):
            result.append(action)
        elif isinstance(action, CascadeAction):
            src_index = action.coord.r * BOARD_N + action.coord.c
            enemy_lost, own_lost = simulate_cascade(state, src_index, action.direction, my_color_int)
            if enemy_lost - own_lost > 0:
                result.append(action)
    return result