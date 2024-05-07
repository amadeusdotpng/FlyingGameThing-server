from math import sin, cos
from math import radians as rad
from flask import Flask, jsonify, Response, request
from random import choice
import numpy as np
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
        'dir': {'x': x, 'y': y, 'z': z},
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
    if 'uuid' not in request:
        return Response(status=400)

    player_uuid = request['uuid']
    data = players[player_uuid]
    resp = jsonify(data)
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

# default Godot _physics_process() delta value
DELTA: float = 1/60
@app.route('/set_data')
def set_data():
    # We're only going to send ACTIONS to the server, i.e. we send 
    # only things we WANT to do. We never want the client to have
    # the authority of telling the server what the game state should
    # look like, otherwise we easily get cheaters. In our case, we
    # send the client's current acceleration and rotation movement.
    # However, because it takes a lot of math and I'm lazy, we're
    # going to be sending the direction the plane is facing instead
    # of calculating it.
    #
    # The server then calculates what the next game state 
    # should be and sends it back to the client.
    if ('uuid' not in request or
        ('acc' not in request and 0 <= request['acc'] <= 2) or
        ('dir' not in request and len(request['dir']) != 3) or
        'timestamp' not in request):
        return Response(status=400)


    player = players[request['uuid']]

    if int(request['timestamp']) < int(player['timestamp']):
        return Response(status=204)

    acc = request['acc']
    dir = request['dir']

    player['dir'] = request['dir']
    player['vel']['x'] += dir['x'] * SPEED[acc] * DELTA
    player['vel']['y'] += dir['y'] * SPEED[acc] * DELTA
    player['vel']['z'] += dir['z'] * SPEED[acc] * DELTA

    player['pos']['x'] += player['vel']['x'] * DELTA
    player['pos']['y'] += player['vel']['y'] * DELTA
    player['pos']['z'] += player['vel']['z'] * DELTA

    return Response(status=204)

@app.route('/connect')
def connect():
    player_uuid = str(uuid.uuid4())
    players[player_uuid] = {}
    players[player_uuid]['username'] = choice(names)
    players[player_uuid]['pos'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['vel'] = {'x': 0, 'y': 0, 'z': 0}
    players[player_uuid]['rot'] = {'x': 0, 'y': 0, 'z': 0}
    return Response(response=player_uuid, status=201)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
