from referee.game.constants import BOARD_N, MAX_TURNS, PLACEMENT_TURNS, INITIAL_STACK_HEIGHT
from referee.game import PlaceAction, MoveAction, EatAction, CascadeAction, Coord, Direction, PlayerColor

CENTRE = 128
BOARD_N_2 = BOARD_N * BOARD_N

PLACE = "P"
MOVE = "M"
EAT = "E"
CASCADE = "C"

DIRECTIONS = ((-BOARD_N, Direction.Up, 0), (BOARD_N, Direction.Down, 0), (-1, Direction.Left, -1), (1, Direction.Right, 1))


class State:
    __slots__ = ("board",
             "red_tokens",
             "red_stacks",
             "blue_tokens",
             "blue_stacks",
             "red_turn",
             "placement_count",
             "playturn_count",
             "prev_actions",)
    
    def __init__(self):
        self.board = bytearray([CENTRE] * BOARD_N_2)
        self.red_tokens = 0
        self.red_stacks = 0
        self.blue_tokens = 0
        self.blue_stacks = 0
        self.red_turn = True
        self.placement_count = 0
        self.playturn_count = 0
        self.prev_actions = []

    def _apply_place(self, coord):
        board_index = coord.r*BOARD_N + coord.c
        was_red = self.red_turn
        action_log = (PLACE, board_index, was_red)

        if was_red :
            self.board[board_index] += INITIAL_STACK_HEIGHT
            self.red_tokens += INITIAL_STACK_HEIGHT
            self.red_stacks += 1
        else :
            self.board[board_index] -= INITIAL_STACK_HEIGHT
            self.blue_tokens += INITIAL_STACK_HEIGHT
            self.blue_stacks += 1

        self.red_turn = not was_red
        self.placement_count += 1
        self.prev_actions.append(action_log)

    def _apply_move(self, coord, direction):
        board_index = coord.r*BOARD_N + coord.c
        was_red = self.red_turn
        move_stack_delta = self.board[board_index] - CENTRE
        target_index = board_index + direction.r*BOARD_N + direction.c
        action_log = (MOVE, board_index, was_red, move_stack_delta, target_index)

        self.board[board_index] = CENTRE
        if self.board[target_index] != CENTRE:
            if was_red:
                self.red_stacks -= 1
            else:
                self.blue_stacks -= 1
        self.board[target_index] += move_stack_delta

        self.red_turn = not was_red
        self.playturn_count += 1
        self.prev_actions.append(action_log)

    def _apply_eat(self, coord, direction):
        board_index = coord.r*BOARD_N + coord.c
        was_red = self.red_turn
        target_index = board_index + direction.r*BOARD_N + direction.c
        eaten_stack_delta = self.board[target_index] - CENTRE
        action_log = (EAT, board_index, was_red, eaten_stack_delta, target_index)
        
        if was_red:
            self.blue_stacks -= 1
            self.blue_tokens += eaten_stack_delta
        else:
            self.red_stacks -= 1
            self.red_tokens -= eaten_stack_delta
        self.board[target_index] = self.board[board_index]
        self.board[board_index] = CENTRE

        self.red_turn = not was_red
        self.playturn_count += 1
        self.prev_actions.append(action_log)
    
    def _apply_cascade(self, coord, direction):
        board_index = coord.r*BOARD_N + coord.c
        was_red = self.red_turn
        tokens_and_stacks = (self.red_tokens, self.red_stacks, self.blue_tokens, self.blue_stacks)

        save_scan = [(board_index, self.board[board_index])]
        row = board_index // BOARD_N
        increment = direction.r*BOARD_N + direction.c
        cascade_len = abs(self.board[board_index] - CENTRE)
        single_stack = (CENTRE + 1) if was_red else (CENTRE - 1)
        next_index = board_index + increment

        self.board[board_index] = CENTRE
        if was_red:
            self.red_stacks -= 1
        else:
            self.blue_stacks -= 1

        # board_index gets mutated directly
        while True:
            board_index += increment
            if not (0 <= board_index < BOARD_N_2):
                break
            if (direction.c != 0) and ((board_index // BOARD_N) != row):
                break
            save_scan.append((board_index, self.board[board_index]))
        action_log = (CASCADE, was_red, tuple(save_scan), tokens_and_stacks)

        for i in range(cascade_len):
            if (not (0 <= next_index < BOARD_N_2)) or ((direction.c != 0) and (next_index // BOARD_N != row)):
                token_lost = cascade_len - i
                if was_red:
                    self.red_tokens -= token_lost
                else:
                    self.blue_tokens -= token_lost
                break

            if self.board[next_index] != CENTRE:
                self._recursive_push(next_index, increment, row, direction.c)

            self.board[next_index] = single_stack
            if was_red:
                self.red_stacks += 1
            else:
                self.blue_stacks += 1

            next_index += increment

        self.red_turn = not was_red
        self.playturn_count += 1
        self.prev_actions.append(action_log)

    def _recursive_push(self, board_index, increment, row, dir_c):
        current_cell = self.board[board_index]
        next_index = board_index + increment

        if (not (0 <= next_index < BOARD_N_2)) or ((dir_c != 0) and (next_index // BOARD_N != row)):
            if current_cell > CENTRE:
                self.red_tokens -= current_cell - CENTRE
                self.red_stacks -= 1
            else:
                self.blue_tokens += current_cell - CENTRE
                self.blue_stacks -= 1
            self.board[board_index] = CENTRE
            return
        
        if self.board[next_index] != CENTRE:
            self._recursive_push(next_index, increment, row, dir_c)

        self.board[next_index] = current_cell
        self.board[board_index] = CENTRE

    def apply(self, action):
        match action:
            case PlaceAction(coord):
                self._apply_place(coord)
            case MoveAction(coord, direction):
                self._apply_move(coord, direction)
            case EatAction(coord, direction):
                self._apply_eat(coord, direction)
            case CascadeAction(coord, direction):
                self._apply_cascade(coord, direction)
            case _:
                raise ValueError(f"unknown action: {action}")

    def undo(self):
        prev_action = self.prev_actions.pop()
        action = prev_action[0]
        if action == PLACE:
            _, board_index, was_red = prev_action
            self.placement_count -= 1
            self.red_turn = was_red
            if was_red :
                self.red_tokens -= INITIAL_STACK_HEIGHT
                self.red_stacks -= 1
            else :
                self.blue_tokens -= INITIAL_STACK_HEIGHT
                self.blue_stacks -= 1
            self.board[board_index] = CENTRE

        elif action == MOVE:
            _, board_index, was_red, move_stack_delta, target_index = prev_action
            self.playturn_count -= 1
            self.red_turn = was_red
            self.board[target_index] -= move_stack_delta
            if self.board[target_index] != CENTRE:
                if was_red:
                    self.red_stacks += 1
                else:
                    self.blue_stacks += 1
            self.board[board_index] += move_stack_delta

        elif action == EAT:
            _, board_index, was_red, eaten_stack_delta, target_index = prev_action
            self.playturn_count -= 1
            self.red_turn = was_red
            self.board[board_index] = self.board[target_index]
            self.board[target_index] = CENTRE + eaten_stack_delta
            if was_red:
                self.blue_stacks += 1
                self.blue_tokens -= eaten_stack_delta
            else:
                self.red_stacks += 1
                self.red_tokens += eaten_stack_delta

        elif action == CASCADE:
            _, was_red, save_scan, token_and_stacks = prev_action
            self.playturn_count -= 1
            self.red_turn = was_red
            for index, byte in save_scan:
                self.board[index] = byte
            (self.red_tokens, self.red_stacks, self.blue_tokens, self.blue_stacks) = token_and_stacks
        else:
            raise ValueError(f"unknown action tag in undo: {action}")
        

    def legal_actions(self):
        legal_list = []
        if self.placement_count == 0:
            for i in range(BOARD_N_2):
                legal_list.append(PlaceAction(Coord(i // BOARD_N, i % BOARD_N)))
        elif self.placement_count < PLACEMENT_TURNS:
            is_red = self.red_turn
            for i in range(BOARD_N_2):
                if self.board[i] != CENTRE: continue
                r, c = i // BOARD_N, i % BOARD_N
                if is_red:
                    if (r > 0) and (self.board[i - BOARD_N] < CENTRE): continue
                    if (r < BOARD_N - 1) and (self.board[i + BOARD_N] < CENTRE): continue
                    if (c > 0) and (self.board[i - 1] < CENTRE): continue
                    if (c < BOARD_N - 1) and (self.board[i + 1] < CENTRE): continue
                else:
                    if (r > 0) and (self.board[i - BOARD_N] > CENTRE): continue
                    if (r < BOARD_N - 1) and (self.board[i + BOARD_N] > CENTRE): continue
                    if (c > 0) and (self.board[i - 1] > CENTRE): continue
                    if (c < BOARD_N - 1) and (self.board[i + 1] > CENTRE): continue
                legal_list.append(PlaceAction(Coord(r, c)))
        else:
            is_red = self.red_turn
            
            for i in range(BOARD_N_2):
                if is_red:
                    if self.board[i] <= CENTRE: continue
                else:
                    if self.board[i] >= CENTRE: continue

                r, c = i // BOARD_N, i % BOARD_N
                current_cell = self.board[i] - CENTRE

                for direction in DIRECTIONS:
                    target_index = i + direction[0]
                    if not (0 <= target_index < BOARD_N_2): continue
                    if (direction[2] != 0) and (target_index // BOARD_N != r): continue

                    target_cell = self.board[target_index] - CENTRE

                    if abs(current_cell) > 1:
                        legal_list.append(CascadeAction(Coord(r, c), direction[1]))    
                    if (target_cell == 0) or (target_cell*current_cell > 0):
                        legal_list.append(MoveAction(Coord(r, c), direction[1]))
                    elif abs(current_cell) >= abs(target_cell):
                        legal_list.append(EatAction(Coord(r, c), direction[1]))

        return legal_list
    
    def game_finished(self):
        if self.placement_count < PLACEMENT_TURNS: return False
        if (self.red_tokens == 0): return True
        if (self.blue_tokens == 0): return True
        if (self.playturn_count >= MAX_TURNS): return True
        if not (self.legal_actions()): return True
        return False
    
    def winner(self):
        if self.game_finished():
            if self.red_tokens > self.blue_tokens: return PlayerColor.RED
            if self.blue_tokens > self.red_tokens: return PlayerColor.BLUE
        return None

    # extra function for MCTS 
    # (cloning new states and throwing them away after is better than tracking undo for MCTS)
    def clone(self):
        new = State.__new__(State)
        new.board = bytearray(self.board)
        new.red_tokens = self.red_tokens
        new.red_stacks = self.red_stacks
        new.blue_tokens = self.blue_tokens
        new.blue_stacks = self.blue_stacks
        new.red_turn = self.red_turn
        new.placement_count = self.placement_count
        new.playturn_count = self.playturn_count
        new.prev_actions = []
        return new