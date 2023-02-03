#!/usr/bin/env python3.11
# Imports
import sys
import json
import asyncio
import aiohttp
import requests
import traceback
import discord
from discord.ext import tasks

debug = False

#########################################################################################
# Requirements for Discord Bot
#########################################################################################

# Read config file
with open("config.json", 'r') as jsonfile:
   config_data = json.load(jsonfile)
   token = config_data.get("discord_token")

# Check if Token is valid
r = requests.get("https://discord.com/api/v10/users/@me", headers={
    "Authorization": f"Bot {token}"
})

# If the token is correct, it will continue the code
data = r.json()

if not data.get("id", None):
   print("/n".join(["ERROR: Token is not valid!"]))
   sys.exit(False)

update_interval = int(config_data.get("update_interval"))*60

# Welcome in console
print("\n".join([
   "Starting Discord Bot..."
]))

#########################################################################################
# Start Up
#########################################################################################

# A Basic Discord Bot Client
client = discord.Client(intents = discord.Intents.default())

@client.event
async def on_ready():
    """ This is called when the bot is ready and has a connection with Discord
        It also prints out the bot's invite URL that automatically uses your
        Client ID to make sure you invite the correct bot with correct scopes.
    """
    print("\n".join([
        f"Logged in as {client.user} (ID: {client.user.id})",
        "",
        f"Use this URL to invite {client.user} to your server:",
        f"https://discord.com/api/oauth2/authorize?client_id={client.user.id}&scope=applications.commands%20bot"
    ]))

    client.loop.create_task(statusloop())

#########################################################################################
# Functions
#########################################################################################

# Loop every update_interval in minutes
@tasks.loop(seconds=update_interval)
async def statusloop():
   while True:
      # API Call
      try:
         # Check what API is used
         match config_data.get("use_api"):
            # Battlemetrics
            case "1":
               async with aiohttp.ClientSession() as session:
                  async with session.get(config_data.get("api_url_battlemetrics")) as response:
                     if response.status == 200:
                        if debug:
                           print("> Battlemetrics API Request successful")
                        rust_server_status_bm = await response.json()
                        status = rust_server_status_bm["data"]["attributes"].get("status")
                        current_players = rust_server_status_bm["data"]["attributes"].get("players")
                        max_players = rust_server_status_bm["data"]["attributes"].get("maxPlayers")
                        queued_players = rust_server_status_bm["data"]["attributes"]["details"].get("rust_queued_players")
                        last_wipe = rust_server_status_bm["data"]["attributes"]["details"].get("rust_last_wipe").split("T")[0].split("-")
                     else:
                        print(f"> Failed to update Battlemetrics API: {response.status}\n")

               # Check status and create activity string
               if status == "online":
                  if int(queued_players) > 0:
                     activitymessage = f"{current_players}/{max_players} (+{queued_players}) | Wipe: {last_wipe[2]}.{last_wipe[1]}."
                  else:
                     activitymessage = f"{current_players}/{max_players} | Wipe: {last_wipe[2]}.{last_wipe[1]}."
               elif status == "offline":
                  activitymessage = f"offline | Wipe: {last_wipe[2]}.{last_wipe[1]}."

            # rust-servers.net
            case "2":
               async with aiohttp.ClientSession() as session:
                  async with session.get(config_data.get("api_url_rust-servers")) as response:
                     if response.status == 200:
                        if debug:
                           print("> rust-servers.net API Request successful")
                        rust_server_status_rs = await response.json(content_type="text/html; charset=utf-8")
                        status = rust_server_status_rs.get("is_online")
                        current_players = rust_server_status_rs.get("players")
                        max_players = rust_server_status_rs.get("maxplayers")
                     else:
                        print(f"> Failed to update rust-servers.net API: {response.status}\n")

               # Check status and create activity string
               if status == "1":
                  activitymessage = f"{current_players}/{max_players}"
               else:
                  activitymessage = "offline"

         # Send new Status Message
         await client.change_presence(status=discord.Status.online, activity=discord.Game(name=activitymessage))

         # Wait for update interval
         await asyncio.sleep(update_interval)

      except Exception:
         print(f"> Exception occured processing Rust Server Status: {traceback.print_exc()}")

@statusloop.before_loop
async def statusloop_before_loop():
   # Wait until Discord Server is ready then start statusloop
   await client.wait_until_ready()


#########################################################################################
# Server Start
#########################################################################################

# Runs the bot with the token you provided
client.run(token)
