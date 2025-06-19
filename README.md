# Welcome to the simple Rust Server Status Discord Bot
It uses battlemetrics.com API to show your Rust Server Status as a Discord Bot Status.  

### before you launch yourself!
It is important, that you create your own Bot by creating a New Application at https://discord.com/developers/applications.  
Afterwards go to the "Bot" Section and create the Bot.  
Finally it is important to press "Reset Token" to receive your token for your Bot.  
Put this token now into the token file. Now you're able to launch the bot!  

This Music Bot requires python3 and python venv(tested on 3.11 and 3.13) https://www.python.org/downloads/  
Install python requirements using:  
* python3 -m venv discord-music-venv
* source discord-music-venv/bin/activate
* pip install -r requirements.txt
* python index.py / sh start.sh (for a screen session)

Also check config.json and addapt discord_token and api_url with your settings.  
