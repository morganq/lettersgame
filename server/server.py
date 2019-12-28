import asyncio
import json
import logging
import websockets
import random
import time
import socket
import requests
from player import Player
from game import Game

logging.basicConfig()

NEXT_ID = 1
games = []
player_for_websocket = {}
game_for_player = {}

def get_users():
    return list(player_for_websocket.values())

def state_event(game):
    s = game.serialize()
    return json.dumps({"type": "state", "value": s})

def join_event(player_id):
    return json.dumps({"type":"joined", "value": {"your_id":player_id}})

def move_player(player, x, y):
    player.x = x
    player.y = y

def set_player_target(player, tx, ty):
    player.tx = tx
    player.ty = ty

async def notify_state(game):
    if player_for_websocket:  # asyncio.wait doesn't accept an empty list
        ws_for_player = dict(map(reversed, player_for_websocket.items())) # invert dict
        message = state_event(game)
        await asyncio.wait([ws_for_player[p].send(message) for p in game.players])

async def register(websocket):
    global NEXT_ID
    p = Player(NEXT_ID)
    NEXT_ID += 1

    # Find a game for this player
    games_random = list(games)
    random.shuffle(games_random)
    game = None
    for game in games_random:
        if len(game.players) < game.max_players:
            game.add_player(p)
            if len(game.players) == 3:
                game.new_round()
            break
    else: # if we didn't find an existing game
        game = Game()
        game.add_player(p)
        games.append(game)
    
    game_for_player[p] = game

    player_for_websocket[websocket] = p

    await notify_state(game)

async def unregister(websocket):
    p = player_for_websocket[websocket]
    game = game_for_player[p]
    game.players.remove(p)
    del player_for_websocket[websocket]
    if len(game.players) == 0:
        games.remove(game)
    else:
        await notify_state(game)


async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        player = player_for_websocket[websocket]
        player_id = player.pid
        game = game_for_player[player]

        await websocket.send(join_event(player_id))
        await websocket.send(state_event(game))
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "move":
                move_player(player, data['x'], data['y'])
            if data["action"] == "target":
                set_player_target(player, data['x'], data['y'])
            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)

async def main():
    t1 = asyncio.create_task(update_game())
    t2 = asyncio.create_task(print_status())

async def update_game():
    target_dt = 0.1
    last_time = time.time()
    while 1:
        current_time = time.time()
        dt = current_time - last_time
        next_tick = current_time + target_dt
        for game in games:
            game.update(dt)
            await notify_state(game)
        last_time = time.time()
        await asyncio.sleep(next_tick - time.time())

async def print_status():
    while 1:
        print("-- Status --")
        for game in games:
            print(game.status_str())
        await asyncio.sleep(5)

host_ip = None
try:
    content = requests.get("http://checkip.amazonaws.com").content
    host_ip = content.decode('iso-8859-1').strip()
    start_server = websockets.serve(counter, host_ip, 6789)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_until_complete(main())
    print("Hosting on %s" % host_ip)
    asyncio.get_event_loop().run_forever()
except Exception as e:
    print(e)
    host_ip = socket.gethostbyname(socket.gethostname())
    start_server = websockets.serve(counter, host_ip, 6789)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_until_complete(main())
    print("Hosting on %s" % host_ip)
    asyncio.get_event_loop().run_forever()    