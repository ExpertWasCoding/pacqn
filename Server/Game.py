import numpy as np
from collections import deque
import random
import torch
import torch.nn as nn
import torch.optim as optim

boardtypes = [
    [
        "############################",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#o####.#####.##.#####.####o#",
        "#.####.#####.##.#####.####.#",
        "#..........................#",
        "#.####.##.########.##.####.#",
        "#.####.##.########.##.####.#",
        "#......##....##....##......#",
        "######.##### ## #####.######",
        "######.##### ## #####.######",
        "######.##          ##.######",
        "######.## ###  ### ##.######",
        "######.## #  b   # ##.######",
        " p     ##   c  d   ##       ",
        "######.## #   a  # ##.######",
        "######.## ###  ### ##.######",
        "######.##          ##.######",
        "######.## ######## ##.######",
        "######.## ######## ##.######",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#.####.#####.##.#####.####.#",
        "#o..##................##..o#",
        "###.##.##.########.##.##.###",
        "###.##.##.########.##.##.###",
        "#......##....##....##......#",
        "#.##########.##.##########.#",
        "#.##########.##.##########.#",
        "#..........................#",
        "############################"
    ]
]

class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_size)
        )
        
    def forward(self, x):
        return self.network(x)

class PacmanAI:
    def __init__(self):
        self.state_size = 31 * 28
        self.action_size = 4
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        self.model = DQN(self.state_size, self.action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()
        
        try:
            self.model.load_state_dict(torch.load('pacman_model.pth'))
            self.model.eval()
        except:
            print("Starting with new model")

    def get_state(self, board):
        state = []
        for row in board:
            for cell in row:
                if cell == '#':
                    state.append(1)
                elif cell == '.':
                    state.append(0.5)
                elif cell in ['a', 'b', 'c', 'd']:
                    state.append(-1)
                elif cell == 'p':
                    state.append(0.75)
                else:
                    state.append(0)
        return torch.FloatTensor(state)

class GhostAI:
    def __init__(self):
        self.directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    
    def get_pacman_position(self, board):
        for i in range(len(board)):
            for j in range(len(board[i])):
                if board[i][j] == 'p':
                    return (i, j)
        return None
    
    def get_ghost_positions(self, board):
        ghosts = {}
        for i in range(len(board)):
            for j in range(len(board[i])):
                if board[i][j] in ['a', 'b', 'c', 'd']:
                    ghosts[board[i][j]] = (i, j)
        return ghosts
    
    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def is_valid_move(self, board, ghost_pos, direction):
        new_pos = (ghost_pos[0] + direction[0], ghost_pos[1] + direction[1])
        if (0 <= new_pos[0] < len(board) and 
            0 <= new_pos[1] < len(board[0]) and 
            board[new_pos[0]][new_pos[1]] != '#'):
            return True
        return False

class Player:
    def __init__(self, player_pos):
        self.points = 0
        self.x = player_pos[0]
        self.y = player_pos[1]
        self.player_pos = [self.x, self.y]
        self.ai = PacmanAI()

    def __getitem__(self, index):
        return self.player_pos[index]
    
    def get_ai_move(self, board):
        state = self.ai.get_state(board)
        return self.ai.act(state)
    
    def move(self, board, move):
        if move == "up":
            if board[self.x-1,self.y] in "abcd":
                return 'death'
            if board[self.x-1,self.y] != '#':
                if board[self.x-1,self.y] == '.':
                    self.points += 1
                board[self.x,self.y] = ' '
                self.x -= 1
                board[self.x,self.y] = 'p'
                if board[self.x,self.y] == '.':
                    self.points += 1
               
        if move == "down":
            if board[self.x+1,self.y] in "abcd":
                return 'death'
            elif board[self.x+1,self.y] != '#':
                if board[self.x+1,self.y] == '.':
                    self.points += 1
                board[self.x,self.y] = ' '
                self.x += 1
                board[self.x,self.y] = 'p'
                
        if move == "left":
            if board[self.x,self.y-1] in "abcd":
                return 'death'
            elif board[self.x,self.y-1] != '#':
                if board[self.x,self.y-1] == '.':
                    self.points += 1
                board[self.x,self.y] = ' '
                self.y -= 1
                board[self.x,self.y] = 'p'
                
        if move == "right":
            if board[self.x,self.y+1] in "abcd":
                return 'death'
            elif board[self.x,self.y+1] != '#':
                if board[self.x,self.y+1] == '.':
                    self.points += 1 
                board[self.x,self.y] = ' '
                self.y += 1
                board[self.x,self.y] = 'p'


class Ghost:
    def __init__(self, ghost_pos, id):
        self.x = ghost_pos[0]
        self.y = ghost_pos[1]
        self.id = id
        self.position = [self.x, self.y]
        self.last_block = ' '

    def move(self, board, move):
        if move == "up":
            if board[self.x - 1, self.y] == 'p':
                return 'death'
            elif board[self.x - 1, self.y] not in "abcd#":
                board[self.x, self.y] = self.last_block
                self.last_block = board[self.x - 1, self.y]
                self.x -= 1
                board[self.x, self.y] = self.id
           
        if move == "down":
            if board[self.x + 1, self.y] == 'p':
                return 'death'
            elif board[self.x + 1, self.y] not in "abcd#":
                board[self.x, self.y] = self.last_block
                self.last_block = board[self.x + 1, self.y]
                self.x += 1
                board[self.x, self.y] = self.id

class Board:
    def __init__(self):
        global rows, cols
        rand = random.randint(0, len(boardtypes)-1)
        arr = boardtypes[rand]
        self.rand = rand
        np_board = np.array([list(row) for row in arr])
        self.board = np_board
        self.row, self.col = self.board.shape
        self.positions = self.get_positions()
        rows, cols = self.row, self.col

    def get_positions(self):
        positions = {'player': None, 'ghosts': []}
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.board[i][j] == 'p':
                    positions['player'] = (i, j)
                elif self.board[i][j] in ['a', 'b', 'c', 'd']:
                    positions['ghosts'].append((i, j))
        return positions
 
