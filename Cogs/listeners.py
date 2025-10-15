import discord
from discord.ext import commands

from Tools.DBCables import Cables

sqldb= Cables("celestia_datastore.db")

async def snipe_user(message: discord.Message):
    member= message.author
    if member and not member.bot:
        await sqldb.set_u_snipe(member.id, message.content)

async def snipe_guild(message: discord.Message):
    guild= message.guild
    member= message.author
    if member and guild and not member.bot:
        await sqldb.set_g_snipe(guild.id, str(member.id)+ ':'+ message.content)

class ListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
##############################################

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await sqldb.connect()

        await snipe_user(message)
        await snipe_guild(message)

##############################################
async def setup(bot: commands.Bot) -> None:
 	await bot.add_cog(ListenerCog(bot))
