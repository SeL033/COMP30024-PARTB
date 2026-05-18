import random
from .board import BOARD_N_2

# Seed for reproducibility
random.seed(0xC45CADE)

# Transposition table entry flags
EXACT = 0
LOWER = 1
UPPER = 2

_HASH_BITS = 64
_NUM_BYTE_VALUES = 256

# Zobrist hashing: each (cell_index, byte_value) pair gets a unique random 64-bit number.
# The board hash is the XOR of all occupied cells' Zobrist values.
_ZOBRIST = [[random.getrandbits(_HASH_BITS) for _ in range(_NUM_BYTE_VALUES)] for _ in range(BOARD_N_2)]

# Extra Zobrist values for turn and placement phase to distinguish otherwise identical boards
_ZOBRIST_TURN = random.getrandbits(_HASH_BITS)
_ZOBRIST_PLACEMENT = [random.getrandbits(_HASH_BITS) for _ in range(9)]

class TTEntry:
    # A single transposition table entry storing search results for a position
    __slots__ = ('depth', 'value', 'flag', 'best_action')
    def __init__(self, depth, value, flag, best_action):
        self.depth = depth
        self.value = value
        self.flag = flag
        self.best_action = best_action
        
def hash_state(state):
    # Compute a Zobrist hash of the current board state.
    # XOR the Zobrist value for each cell's byte, plus turn and placement phase.
    h = 0
    for i in range(BOARD_N_2):
        h ^= _ZOBRIST[i][state.board[i]]
    if state.red_turn:
        h ^= _ZOBRIST_TURN
    h ^= _ZOBRIST_PLACEMENT[state.placement_count]
    return h