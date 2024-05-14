from flask import Flask, jsonify, Response, redirect, request
from random import choice
from enum import Enum
import uuid
import time

# Godly resource: 
# https://gabrielgambetta.com/client-server-game-architecture.html

# Setup
app = Flask(__name__)

# Global Lobby
# The structure should be:
"""
{
    start_time: float
    end_time: float
    restart_time: float
    game_state: GameState
    'players': {
        player_uuid: {
            'username': str,
            'last_updated': float,
            'finish_time': float,
            'finished': bool,

            'rot': {'x': float, 'y': float, 'z': float},
            'pos': {'x': float, 'y': float, 'z': float},
            'vel': {'x': float, 'y': float, 'z': float}, 
            'acc': {'x': float, 'y': float, 'z': float}, 
        }
    }
}
"""

class GameState(str, Enum):
    WARMUP  = 'WARMUP'
    STARTED = 'STARTED'
    ENDED   = 'ENDED'

names = [
    'Foo', 'Bar', 'Baz', 'Qux', 'Quux', 'Plugh', 'Xyzzy',
    'Hoge', 'Fuga', 'Piyo', 'Hogera', 'Hogehoge',
    'Toto', 'Hede', 'Hodo', 'Pippo', 'Pluto',
    'Spam', 'Ham', 'Eggs',
    'Alice', 'Bob', 'Charlie', 'Eve',
]

START_TIME = 45                             # 45 sec warmup
END_TIME = START_TIME + 2*60+30             # 2.5 minuts to finish the race
RESTART_TIME = START_TIME + END_TIME + 10   # 10 sec chill sesh
current_time = time.time()
lobby = {
    'start_time': current_time + START_TIME,
    'end_time': current_time + END_TIME,
    'restart_time':current_time + RESTART_TIME,
    'game_state': GameState.WARMUP,  # start it on warm u[
    'players': {},
}

def clean():
    current_time = time.time()
    players = lobby['players']
    disconnected_players = [uuid for uuid in players if current_time - players[uuid]['last_updated'] > 60]
    for uuid in disconnected_players:
        del lobby['players'][uuid]

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/get_data')
def get_data():
    clean()
    if (lobby['game_state'] == GameState.WARMUP and
        lobby['start_time'] < time.time()):
        lobby['game_state'] = GameState.STARTED

    if (lobby['game_state'] == GameState.STARTED and
        (lobby['end_time'] < time.time() or 
         all(lobby['players'][uuid]['finished'] for uuid in lobby['players']))):
        lobby['game_state'] = GameState.ENDED

    if (lobby['game_state'] == GameState.ENDED and
        lobby['restart_time'] < time.time()):

        reset_lobby()

    resp = jsonify(lobby)
    resp.status_code = 200
    return resp

# In-game constants
# -----------------
@app.route('/set_data', methods=['POST'])
def set_data():
    data = request.get_json()

    conditions = ['last_updated', 'uuid', 'finished', 'rot', 'pos', 'vel', 'acc']
    if data is None or any(c not in data for c in conditions):
        return Response(response='Bad Data', status=400)

    if data['uuid'] not in lobby['players']:
        player_info = create_player()
        data['uuid'] = player_info['uuid']

    player = lobby['players'][data['uuid']]

    player['last_updated'] = data['last_updated']

    player['rot'] = data['rot']
    player['pos'] = data['pos']
    player['vel'] = data['vel']
    player['acc'] = data['acc']

    if data['finished'] and lobby['game_state'] == GameState.STARTED:
        player['finish_time'] = time.time()
        player['finished'] = True

    return Response(response='Success', status=200)


@app.route('/connect')
def connect():
    clean()
    if len(lobby['players']) == 0:
        lobby['start_time'] = time.time() + START_TIME
        lobby['end_time'] = time.time() + END_TIME
        lobby['game_state'] = GameState.WARMUP


    gamestate_time = None
    match lobby['game_state']:
        case GameState.WARMUP: gamestate_time = lobby['start_time']
        case GameState.STARTED: gamestate_time = lobby['end_time']
        case GameState.ENDED:   gamestate_time = lobby['restart_time']

    player_info = create_player()
    player_info['gamestate_time'] = gamestate_time

    resp = jsonify(player_info)
    resp.status_code = 201
    return resp

def create_player():
    player_uuid = str(uuid.uuid4())
    username = choice(names)
    players = lobby['players']
    players[player_uuid] = {}
    players[player_uuid]['username'] = username
    players[player_uuid]['last_updated'] = time.time()
    players[player_uuid]['finish_time'] = -1
    players[player_uuid]['finished'] = False

    players[player_uuid]['rot'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['pos'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['vel'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['acc'] = {'x': 0, 'y': 0, 'z': 0}

    return {'uuid': player_uuid, 'username': username}

def reset_lobby():
    current_time = time.time()
    lobby['start_time'] = current_time + START_TIME
    lobby['end_time'] =  current_time + END_TIME
    lobby['restart_time'] = current_time + RESTART_TIME
    lobby['game_state'] = GameState.WARMUP  # start it on warm u[
    
    for player in lobby['players']:
        player['finish_time'] = -1
        player['finished'] = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
