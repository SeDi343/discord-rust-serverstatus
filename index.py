#!/usr/bin/env python3
# Imports
import sys
import json
import asyncio
import aiohttp
import requests
import traceback
import datetime
from discord import app_commands, Intents, Client, Interaction, Status, Game
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
server_ip = config_data.get("gameserver_ip")
server_port = config_data.get("gameserver_port")

# Welcome in console
print("\n".join([
   "Starting Discord Bot..."
]))

#########################################################################################
# Start Up
#########################################################################################

# Main Class to response in Discord
class ChatResponse(Client):
    def __init__(self):
        super().__init__(intents = Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """ This is called when the bot boots, to setup the global commands """
        await self.tree.sync(guild = None)

# Variable to store the bot class and interact with it
# Since this is a simple bot to run 1 command over slash commands
# We then do not need any intents to listen to events
client = ChatResponse()

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

    await client.tree.sync()
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
         await client.change_presence(status=Status.online, activity=Game(name=activitymessage))

         # Wait for update interval
         await asyncio.sleep(update_interval)

      except Exception:
         print(f"> Exception occured processing Rust Server Status: {traceback.print_exc()}")

# Function for Gameserver connect command response
async def _init_command_ip_response(interaction: Interaction):
    """A gameserver connect command response from the Bot"""

    # Respond in the console that the command has been ran
    print(f"> {interaction.guild} : {interaction.user} used the ip command.")

    # Respond with the connection command
    await interaction.response.send_message("\n".join([
        f"Hey {interaction.user.mention}, following you find the commands for the F1 console to connect to the server",
        "",
        f"**client.connect {server_ip}:{server_port}**"
    ]))

# Function to send donation response
async def _init_command_donation_response(interaction: Interaction):
    """The function to send donation link"""
    try:
        # Respond in the console that the command has been ran
        print(f"> {interaction.guild} : {interaction.user} used the donation command.")

        await interaction.response.send_message("\n".join([
            f"Hey {interaction.user.mention}, thank you for considering donating to support my work!",
            f"You can donate via PayPal using https://donate.aerography.eu/ :heart_hands:"]))
    except Exception:
        print(f" > Exception occured processing donation command: {traceback.format_exc()}")
        await interaction.followup.send(f"Exception occured processing reddit. Please contact <@164129430766092289> when this happened.")
        return await interaction.channel.send(embed=console_create(traceback))

async def _init_command_wipe_response(interaction: Interaction):
    """The fucntion to send the next wipe day"""
    # Respond in the console that the command has been ran
    print(f"> {interaction.guild} : {interaction.user} used the wipe command.")

    today = datetime.date.today()

    # Move to the first day of the next month
    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)

    # Calculate the first Thursday of next month
    days_until_thursday = (3 - next_month.weekday()) % 7
    first_thursday = next_month + datetime.timedelta(days=days_until_thursday)

    # Calculate the first Thursday of this month
    this_month = datetime.date(today.year, today.month, 1)
    days_until_this_thursday = (3 - this_month.weekday()) % 7
    this_first_thursday = this_month + datetime.timedelta(days=days_until_this_thursday)

    if today == this_first_thursday:
        await interaction.response.send_message("\n".join([
            f"Hey {interaction.user.mention},",
            f"der nächste Force Wipe ist am {this_first_thursday.strftime('%d.%m.%Y')} ~ 20:00 Uhr",
            f"the next force wipe is on {this_first_thursday.strftime('%d.%m.%Y')} ~ 08:00 PM"]))
    else:
        await interaction.response.send_message("\n".join([
            f"Hey {interaction.user.mention},",
            f"der nächste Force Wipe ist am {first_thursday.strftime('%d.%m.%Y')} ~ 20:00 Uhr",
            f"the next force wipe is on {first_thursday.strftime('%d.%m.%Y')} ~ 08:00 PM"]))

@statusloop.before_loop
async def statusloop_before_loop():
   # Wait until Discord Server is ready then start statusloop
   await client.wait_until_ready()

# Command to check connect command for gameserver
@client.tree.command()
async def ip(interaction: Interaction):
    """Command to check gameserver connect command"""
    await _init_command_ip_response(interaction)

# Command to check the next wipe day
@client.tree.command()
async def wipe(interaction: Interaction):
    """Command to check the next wipe day"""
    await _init_command_wipe_response(interaction)

# Command for Donation
@client.tree.command()
async def donate(interaction: Interaction):
    """A command to send donation link"""
    await _init_command_donation_response(interaction)

#########################################################################################
# Server Start
#########################################################################################

# Runs the bot with the token you provided
client.run(token)
