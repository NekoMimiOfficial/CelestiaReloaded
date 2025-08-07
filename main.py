import discord
from discord.ext import commands

import asyncio
import os

from NekoMimi import utils as nm
from NekoMimi import reg
import nekos


print(nm.figlet("Celestia", "larry3d"))

token= reg.readCell("celestia")
prefixes= ['c!', 'C!', 'c ', 'C ', "hey honeypie ", "Hey honeypie ", "hey honeypie, ", "Hey honeypie, "]
bot= commands.Bot(command_prefix= prefixes, intents= discord.Intents.all())

#startup tasks
print(f"Starting up Celestia Reloaded")
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

# These 2 commands have always and will always be part of the main script
@bot.tree.command(name= "neko", description= "Returns a random Neko image from nekos.life API")
async def __CMD_nekonoko(ctx: discord.Interaction):
	embed= discord.Embed(color= 0xee90ac)
	embed.set_image(url= nekos.img(target= "neko"))
	embed.set_footer(text= "Powered by nekos.life")
	await ctx.response.send_message(embed= embed)

@bot.tree.command(name= "kitsune", description= "Returns a random Kitsune image from nekos.life API")
async def __CMD_kitsune(ctx: discord.Interaction):
	embed= discord.Embed(color= 0xee90ac)
	embed.set_image(url=nekos.img(target= "fox_girl"))
	embed.set_footer(text= "Powered by nekos.life")
	await ctx.response.send_message(embed= embed)

#import cogs
async def load():
    for file in os.listdir("./Cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"Cogs.{file[:-3]}")
            # await bot.load_extension("jishaku")

async def startup():
    await load()
    await bot.start(token)

asyncio.run(startup())
