import os
import sys
import json
import asyncio
import requests
import websockets
from keep_alive import keep_alive

status = "idle"  # online/dnd/idle

GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SELF_MUTE = os.getenv("SELF_MUTE") == 'true'
SELF_DEAF = os.getenv("SELF_DEAF") == 'true'

usertoken = os.getenv("TOKEN")
if not usertoken:
    print("[ERROR] Please add a token inside Secrets.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

validate = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]


async def joiner(token, status):
    async with websockets.connect('wss://gateway.discord.gg/?v=9&encoding=json') as ws:
        start = json.loads(await ws.recv())
        heartbeat = start['d']['heartbeat_interval'] / 1000  # Convert milliseconds to seconds
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 10",
                    "$browser": "Google Chrome",
                    "$device": "Windows"
                },
                "presence": {
                    "status": status,
                    "afk": False
                }
            },
            "s": None,
            "t": None
        }
        vc = {
            "op": 4,
            "d": {
                "guild_id": GUILD_ID,
                "channel_id": CHANNEL_ID,
                "self_mute": SELF_MUTE,
                "self_deaf": SELF_DEAF
            }
        }
        await ws.send(json.dumps(auth))
        await ws.send(json.dumps(vc))
        # Send initial heartbeat
        await ws.send(json.dumps({"op": 1, "d": None}))

        while True:
            try:
                # Send heartbeat every 'heartbeat' interval
                await asyncio.sleep(heartbeat)
                await ws.send(json.dumps({"op": 1, "d": None}))
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, reconnecting...")
                break  # Exit loop to reconnect

async def run_joiner():
    os.system("clear")
    print(f"Logged in as {username}#{discriminator} ({userid}).")
    while True:
        try:
            await joiner(usertoken, status)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)  # Wait before trying to reconnect

keep_alive()
asyncio.run(run_joiner())
