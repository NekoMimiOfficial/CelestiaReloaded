import discord
from discord.ext import commands
from discord import app_commands

import random
import asyncio
import os, sys
import traceback

from NekoMimi import utils as nm
from NekoMimi import reg
import Tools.DBCables as cables

def randstrgen():
    big_string= "1s2a3f4b5x6c7z8d9y0e"
    final= ""
    for i in range(8):
        final += random.choice(big_string)
    return final

print(nm.figlet("Celestia", "larry3d"))

token= reg.readCell("celestia")
activity= discord.Activity(type= discord.ActivityType.watching, name= "Neko code in c++, cobol and assembly :'3")
prefixes= ['c!', 'C!', 'c ', 'C ', "hey honeypie ", "Hey honeypie ", "hey honeypie, ", "Hey honeypie, "]
bot= commands.Bot(command_prefix= prefixes, intents= discord.Intents.all(), activity= activity, status= discord.Status.idle)

#startup tasks
print(f"Starting up Celestia Reloaded | PID: {os.getpid()}")
print(f"Token: {token}")

@bot.event
async def on_ready():
    try:
        sync= await bot.tree.sync()
        print(f"{len(sync)} commands have been synced !")
        print("Celestia is up and running !")
    except Exception as e:
        print(e)
        exit(22)

@bot.event
async def on_error(event, *args, **kwargs):
    err_id= randstrgen()
    print(f'[ fail ] Ignoring exception with ERR ID ({err_id}) in event {event}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print("-------------------------------------------------------------------")

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    err_id= randstrgen()
    print(f"[ fail ] Unhandled Command Error ({err_id})", file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    print("-------------------------------------------", file=sys.stderr)

    await ctx.send(f"An error occured, please report this to the devs, ERR ID: {err_id}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    err_id= randstrgen()
    send_func = interaction.channel.send

    if isinstance(error, app_commands.MissingPermissions):
        await send_func(f"You do not have the required permissions (`{', '.join(error.missing_permissions)}`) to use this command.", delete_after= 8)
        return

    else:
        print(f"[ fail ] Unhandled Slash Command Error ({err_id})", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        print("-------------------------------------------------", file=sys.stderr)

        await send_func(f"An error occured, please report this to the devs, ERR ID: {err_id}")


#import cogs
async def load():
    for file in os.listdir("./Cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"Cogs.{file[:-3]}")
    await bot.load_extension("jishaku")

async def startup():
    if not os.path.exists("celestia_datastore.db"):
        sqldb= cables.Cables("celestia_datastore.db")
        await sqldb.format()
        await sqldb.close()
    await load()
    await bot.start(token)

asyncio.run(startup())
