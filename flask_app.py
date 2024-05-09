from flask import Flask, jsonify, Response, request
from random import choice
import uuid

# Godly resource: 
# https://gabrielgambetta.com/client-server-game-architecture.html

# Setup
app = Flask(__name__)

# Global Lobby
# The structure should be:
"""
{
    player_uuid: {
        'username': username,
        'timestamp': timestamp,
        'pos': {'x': x, 'y': y, 'z': z},
        'vel': {'x': x, 'y': y, 'z': z}, 
        'acc': {'x': x, 'y': y, 'z': z}, 
        'win_time': win_time,
    }
}
"""

names = [
    'Foo', 'Bar', 'Baz', 'Qux', 'Quux', 'Plugh', 'Xyzzy',
    'Hoge', 'Fuga', 'Piyo', 'Hogera', 'Hogehoge',
    'Toto', 'Hede', 'Hodo', 'Pippo', 'Pluto',
    'Spam', 'Ham', 'Eggs',
    'Alice', 'Bob', 'Charlie', 'Eve',
]
players = {}



@app.route('/clean')
def clean():
    return 'WIP'

@app.route('/get_data')
def get_data():
    resp = jsonify(players)
    resp.status_code = 200
    return resp


# In-game constants
# -----------------
DRAG: float = 0.9825

PITCH_SPEED = 0.0275
YAW_SPEED = 0.0035
ROLL_SPEED = 0.045

IDLE_SPEED: float = 10
FWD_SPEED: float = 120
BCK_SPEED: float = -25
SPEED = [BCK_SPEED, IDLE_SPEED, FWD_SPEED]

# default timer
DELTA = 1/60 * 0.067
@app.route('/set_data', methods=['POST'])
def set_data():
    data = request.get_json()

    if (data is None or 'timestamp' not in data or 'uuid' not in data or
        'pos' not in data or 'vel' not in data or 'acc' not in data):

        return Response(response='Bad Data', status=400)

    player = players[data['uuid']]
    player['pos'] = data['pos']
    player['vel'] = data['vel']
    player['acc'] = data['acc']
    player['timestamp'] = data['timestamp']


    return Response(response='Success', status=200)


@app.route('/connect')
def connect():
    player_uuid = str(uuid.uuid4())
    players[player_uuid] = {}
    players[player_uuid]['username'] = choice(names)
    players[player_uuid]['pos'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['vel'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['acc'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['timestamp'] = 0

    resp = jsonify({'uuid': player_uuid})
    resp.status_code = 201
    return resp



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
