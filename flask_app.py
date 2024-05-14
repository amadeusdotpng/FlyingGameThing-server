from flask import Flask, jsonify, Response, redirect, request
from flask_cors import CORS, cross_origin
from random import choice
from enum import Enum
import uuid
import time

# Godly resource: 
# https://gabrielgambetta.com/client-server-game-architecture.html

# Setup
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

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

UNTIL_STARTED = 5 # 30 second warmup
UNTIL_ENDED = 2.5*60 # 2.5 minutes to complete race
UNTIL_WARMUP = 5 # 10 second chill sesh

lobby = {
    'until_next': time.time() + UNTIL_WARMUP,
    'game_state': GameState.WARMUP,  # start it on warm up
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
    
    # STARTED finished -> ENDED
    if (lobby['game_state'] == GameState.STARTED and
         (lobby['until_next'] < time.time() or
          all(lobby['players'][uuid]['finished'] for uuid in lobby['players']))):
        lobby['game_state'] = GameState.ENDED

        current_time = time.time()
        lobby['until_next'] = current_time + UNTIL_WARMUP

    # ENDED finished -> WARMUP
    elif (lobby['game_state'] == GameState.ENDED and
          lobby['until_next'] < time.time()):
        lobby['game_state'] = GameState.WARMUP

        current_time = time.time()
        lobby['until_next'] = current_time + UNTIL_STARTED
        lobby['start_time'] = current_time + UNTIL_STARTED
        reset_players()

    # WARMUP finished -> STARTED
    elif (lobby['game_state'] == GameState.WARMUP and
        lobby['until_next'] < time.time()):
        lobby['game_state'] = GameState.STARTED

        current_time = time.time()
        lobby['until_next'] = current_time + UNTIL_ENDED

    resp = jsonify(lobby)
    resp.status_code = 200
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    return resp

# In-game constants
# -----------------
@app.route('/set_data', methods=['POST'])
def set_data():
    data = request.get_json()

    conditions = ['last_updated', 'uuid', 'finished', 'rot', 'pos', 'vel', 'acc']
    if data is None or any(c not in data for c in conditions):
        resp = Response(response='Bad Data', status=400)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Origin, X-Requested-With, Accept'
        return resp

    if data['uuid'] not in lobby['players']:
        player_info = create_player()
        data['uuid'] = player_info['uuid']

    player = lobby['players'][data['uuid']]

    player['last_updated'] = data['last_updated']

    player['rot'] = data['rot']
    player['pos'] = data['pos']
    player['vel'] = data['vel']
    player['acc'] = data['acc']

    resp = Response(response='Success', status=200)
    resp.headers['Access-Control-Allow-Origin'] = 'https://amadeusdotpng.github.io'
    resp.headers['Access-Control-Allow-Methods'] = 'POST'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    return resp

@app.route('/win', methods=['POST'])
def win():
    data = request.get_json()
    if 'uuid' not in data or 'finished' not in data:
        resp = Response(response='Bad Data', status=400)
        resp.headers['Access-Control-Allow-Origin'] = 'https://amadeusdotpng.github.io'
        resp.headers['Access-Control-Allow-Methods'] = 'POST'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        return resp


    player = lobby['players'][data['uuid']]
    if data['finished'] and lobby['game_state'] == GameState.STARTED:
        player['finish_time'] = time.time()
        player['finished'] = True

    resp = Response(response='Success', status=200)
    resp.headers['Access-Control-Allow-Origin'] = 'https://amadeusdotpng.github.io'
    resp.headers['Access-Control-Allow-Methods'] = 'POST'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    return resp

@app.route('/connect')
def connect():
    clean()
    if len(lobby['players']) == 0:
        current_time = time.time()
        lobby['until_next'] = current_time + UNTIL_STARTED
        lobby['start_time'] = current_time + UNTIL_STARTED
        lobby['game_state'] = GameState.WARMUP
    player_info = create_player()
    player_info['gamestate_time'] = lobby['until_next']

    resp = jsonify(player_info)
    resp.status_code = 201
    resp.headers['Access-Control-Allow-Origin'] = 'https://amadeusdotpng.github.io'
    resp.headers['Access-Control-Allow-Methods'] = 'POST'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
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

def reset_players():
    players = lobby['players']
    for uuid in lobby['players']:
        players[uuid]['finish_time'] = -1
        players[uuid]['finished'] = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
