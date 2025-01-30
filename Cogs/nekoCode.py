import discord
from discord.ext import commands
import subprocess

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def bash(self, ctx, *, code : str):
        b = subprocess.getoutput('bash -c "'+code+'"')
        emO = f":inbox_tray:Input\n```\n{code}\n```\n:outbox_tray:Output\n```\n{b}\n```"
        embed = discord.Embed(color=0xEE90AC,title='Bash',description=emO)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("<a:greenTick:834019942000885780>")

    @commands.command()
    @commands.is_owner()
    async def guilds(self, ctx):
        g_list= self.bot.guilds
        await ctx.send("## List of guilds:")
        for g in g_list:

            for channel in g.channels:
                if isinstance(channel, discord.TextChannel):
                    first_channel = channel
                    break
            try:
                invite= await first_channel.create_invite(max_age= 300)
                await ctx.send(invite)
            except:
                pass


async def setup(bot):
    await bot.add_cog(Owner(bot))
