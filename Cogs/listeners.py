import discord
from discord.ext import commands

from Tools.DBCables import Cables

sqldb= Cables("celestia_datastore.db")

async def snipe_user(message: discord.Message):
    member= message.author
    if member and not member.bot and not message.content.replace(" ", "").strip() == "":
        await sqldb.set_u_snipe(member.id, message.content)

async def snipe_guild(message: discord.Message):
    guild= message.guild
    member= message.author
    if member and guild and not member.bot and not message.content.replace(" ", "").strip() == "":
        await sqldb.set_g_snipe(guild.id, str(member.id)+ ':'+ message.content)

async def check_init_guild(guild: discord.Guild):
    is_banned= await sqldb.chk_g_ban(guild.id)
    if is_banned:
        channels= guild.text_channels
        if channels and len(channels) > 0:
            await channels[0].send("# Celestia has been banned from being in this guild\nThis bot can not be added nor used in this server, Our team has deemed this server ineligible to receive the services provided by Celestia, Any stored data will be subject to manual review and deletion\nIf you believe that our team has falsely flagged your server please contact us via email: nekomimi@tilde.team\n\n-# This action is usually irreversable")
        await guild.leave()
    await sqldb.init_guild(guild.id, guild.name)

class ListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
##############################################

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await sqldb.connect()

        await snipe_user(message)
        await snipe_guild(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await sqldb.connect()
        
        if message.guild and self.bot.user and not message.author.id == self.bot.user.id:
            await check_init_guild(message.guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await sqldb.connect()

        await check_init_guild(guild)

##############################################
async def setup(bot: commands.Bot) -> None:
 	await bot.add_cog(ListenerCog(bot))
