import os
import platform
import time

import discord
from colorama import Back, Fore, Style
from discord.ext import commands

#
# Start of bot code
client = commands.Bot(command_prefix='.', intents=discord.Intents.all())


async def setup_hook():
  #await client.tree.sync(guild=discord.Object(id='383365467894710272'))
  current_cog = None
  try:
    for cog in [
        "cogs.MakeMessages",
        "cogs.PurgeBot",
        "cogs.DisplayTime",
        "cogs.SchedulePurge",
        "cogs.MinutesPurge",
        "cogs.BotTest",        
        "cogs.Feedback",
    ]:
      current_cog = cog
      await client.load_extension(cog)
  except Exception as e:
    if current_cog:
      print(f"Failed to load extension {current_cog}:", e)
    else:
      print("Failed to load a cog due to an error before loading:", e)


client.setup_hook = setup_hook


@client.event
async def on_ready():
  schedule_purge_cog = client.get_cog("SchedulePurge")
  if schedule_purge_cog:
    await schedule_purge_cog.update_missed_purge_jobs()
  prfx = (Back.BLACK + Fore.GREEN +
          time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET +
          Fore.WHITE + Style.BRIGHT)
  if client is not None and client.user is not None:
    print(prfx + " Logged in as " + Fore.YELLOW + client.user.name)
    print(prfx + " Bot ID " + Fore.YELLOW + str(client.user.id))
    print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
    python_version_msg = (prfx + " Python Version " + Fore.YELLOW +
                          str(platform.python_version()))
    print(python_version_msg)
    synced = await client.tree.sync()
    print(f"{prfx} Slash CMDs Synced {Fore.YELLOW}{len(synced)} Commands")
    print(prfx + " Current Working Directory:" + Fore.YELLOW + os.getcwd())
    print(prfx + " Bot is Logged in and ready")


# Checks to make sure the token is loaded properly for Discord
token = os.getenv("TOKEN")
if token is not None:
  client.run(token)
else:
  print("Token not loaded properly. Check your environment variables.")
