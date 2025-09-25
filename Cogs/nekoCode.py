import discord
from discord.ext import commands
import subprocess

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def bash(self, ctx, *, code : str):
        b = subprocess.getoutput(f"bash -c '{code}'")
        emO = f":inbox_tray:Input\n```\n{code}\n```\n:outbox_tray:Output\n```\n{b}\n```"
        embed = discord.Embed(color=0xEE90AC,title='Bash',description=emO)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == 770344920510103573:
            if message.content.startswith("./"):
                code= message.content.removeprefix("./")
                b = subprocess.getoutput(f"bash -c '{code}'")
                emO = f":inbox_tray:Input\n```\n{code}\n```\n:outbox_tray:Output\n```\n{b}\n```"
                embed = discord.Embed(color=0xEE90AC,title='Bash',description=emO)
                await message.channel.send(embed=embed)

    @commands.command(name= "git")
    @commands.is_owner()
    async def git_push(self, ctx, *, msg):
        b= subprocess.getoutput(f"bash -c \"git {msg}\"")
        emO = f"```\n{b}\n```"
        embed = discord.Embed(color=0xEE90AC,title='Syncing with git remote',description=emO)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def guilds(self, ctx):
        # usually i dont think my bot will be that popular so i wont handle if the message gets too large
        g_list= self.bot.guilds
        body= ""
        for g in g_list:

            for channel in g.channels:
                if isinstance(channel, discord.TextChannel):
                    first_channel = channel
                    break
            try:
                invite= await first_channel.create_invite(max_age= 300)
                body += f"[{g.name} @ {g.id}]({invite})\n"
            except:
                body += f"{g.name} @ {g.id} (failed to get invite)\n"

        embed= discord.Embed(title= "List of guilds that house Celestia", color= 0xEE90AC, description= body)
        await ctx.send(embed= embed)

    @discord.app_commands.command(name= "neofetch", description= "Get the neofetch output of the bot host")
    async def __cmd_neofetch(self, interaction: discord.Interaction):
        cmd= "neofetch|sed 's/\\x1B\\[[0-9;\\?]*[a-zA-Z]//g'"
        out= subprocess.getoutput(f"bash -c {cmd}")
        em0= f"```\n{out}\n```"
        embed= discord.Embed(title= "neofetch", color=0xEE90AC, description= em0)
        await interaction.response.send_message(embed= embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))
