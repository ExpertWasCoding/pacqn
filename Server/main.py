import flask
from Game import Player, Board, Ghost, PacmanAI, GhostAI
import flask_socketio
from flask_socketio import ConnectionRefusedError, disconnect
from flask import request
import os
import random
import string
import time
import argparse
from tokens import get_entry, remove_entry

player_timestamp = None
ghost_timestamp = None
player_time = 0
ghost_time = 0
moves = 0
participant_token = None
participant_id = None

pacman_ai = PacmanAI()
ghost_ai = GhostAI()

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

connected_clients = []
displayconnected = False
player_token = generate_random_string()
ghost_token = generate_random_string()

app = flask.Flask(__name__)
socketio = flask_socketio.SocketIO(app)

from tokenHandler import token_handler
app.register_blueprint(token_handler, url_prefix='/token')

displayids = []
player_move_docked = False
ghost_move_docked = False
player_connected = False
ghost_connected = False
player_id = None
ghost_id = None
player_name = None
ghost_name = None

def initialize():
    global board, player, ghost1, ghost2, ghost3, ghost4, ghosts
    board = Board()
    positions = board.get_positions()
    player = Player(positions[0])
    ghost1 = Ghost(positions[1], "a")
    ghost2 = Ghost(positions[2], "b")
    ghost3 = Ghost(positions[3], "c")
    ghost4 = Ghost(positions[4], "d")
    ghosts = [ghost1, ghost2, ghost3, ghost4]
    socketio.emit('board', [board.get_board(), player.points])

def process_ai_move():
    player_move = player.get_ai_move(board.get_board())
    ghost_moves = ghost1.get_ai_moves(board.get_board())
    handlemove("player", [1 if i == player_move else 0 for i in range(4)])
    handlemove("ghost", ghost_moves)

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/move/player', methods=['POST'])
def player_move():
    move = flask.request.get_json()
    auth = request.headers.get('Authorization')
    if auth:
        token = auth.split(' ')[1]
    else:
        return flask.jsonify({"error":"Missing Token"}), 401
    if token != player_token:
        return flask.jsonify({"error": "Unauthorized"}), 403
    if not player_connected:
        return flask.jsonify({"error": "Player not connected"}), 400
    if hasattr(player, 'ai_mode') and player.ai_mode:
        move = player.get_ai_move(board.get_board())
    handlemove("player", move)
    return flask.jsonify({"status": "success"})

@app.route('/move/ghost', methods=['POST'])
def ghost_move():
    move = flask.request.get_json()
    auth = request.headers.get('Authorization')
    if auth:
        token = auth.split(' ')[1]
    else:
        return flask.jsonify({"error":"Missing Token"}), 401
    if token != ghost_token:
        return flask.jsonify({"error": "Unauthorized"}), 403
    if not ghost_connected:
        return flask.jsonify({"error": "Ghost not connected"}), 400
    if hasattr(ghost1, 'ai_mode') and ghost1.ai_mode:
        move = ghost1.get_ai_moves(board.get_board())
    handlemove("ghost", move)
    return flask.jsonify({"status": "success"})

def handlemove(character_type, move):
    global player_move_docked, ghost_move_docked, player, ghosts, player_connected, ghost_connected, moves
    if character_type == "player":
        if not player_connected:
            return
        player_move_docked = True
        player.move(move)
        moves += 1
        if ghost_connected:
            process_ai_move()
    elif character_type == "ghost":
        if not ghost_connected:
            return
        ghost_move_docked = True
        for i, ghost_move in enumerate(move):
            ghosts[i].move(ghost_move)
        moves += 1
        if player_connected:
            process_ai_move()

@socketio.on('connect')
def on_connect():
    global player_connected, ghost_connected, player_id, ghost_id, player_name, ghost_name
    if player_connected and ghost_connected:
        return
    if not player_connected:
        player_connected = True
        player_id = generate_random_string()
        player_name = 'Player'
        socketio.emit('connected', {"player_id": player_id})
    elif not ghost_connected:
        ghost_connected = True
        ghost_id = generate_random_string()
        ghost_name = 'Ghost'
        socketio.emit('connected', {"ghost_id": ghost_id})

@app.route('/disconnect/player', methods=['POST'])
def player_disconnect():
    global player_connected, player_id
    player_connected = False
    player_id = None
    return flask.jsonify({"status": "Player disconnected"})

@app.route('/disconnect/ghost', methods=['POST'])
def ghost_disconnect():
    global ghost_connected, ghost_id
    ghost_connected = False
    ghost_id = None
    return flask.jsonify({"status": "Ghost disconnected"})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask-SocketIO server.')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()

    extra_files = [
        os.path.join(os.getcwd(), 'static', 'index.js'),
        os.path.join(os.getcwd(), 'templates', 'index.html')
    ]
    
    socketio.run(app, port=5000, debug=True, extra_files=extra_files, host='0.0.0.0')

