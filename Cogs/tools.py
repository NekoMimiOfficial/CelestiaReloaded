import discord
from discord import app_commands
from discord.ext import commands

import asyncio
import nekos

from NekoMimi import utils as nm

class ToolCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
##############################################

    @app_commands.command(name= "emoji", description= "Shows the emoji by typing its name eliminating the need for nitro to view gif emotes")
    @app_commands.describe(emote= "Enter an emote name from this server")
    async def __CMD_emoji(self, interaction: discord.Interaction, emote: str):
        if emote.startswith("<:"):
            emote= emote.split(":")[1]

        try:
            mojo= discord.utils.get(interaction.guild.emojis, name= emote) #type: ignore
        except Exception:
            await interaction.response.send_message("This emoji name seems to not exist", ephemeral= True)
            return

        if mojo is None:
            await interaction.response.send_message("This emoji name seems to not exist", ephemeral= True)
            return

        _url= mojo.url
        _name= mojo.name
        _id= mojo.id
        _timestamp= mojo.created_at
        footerText= f"`<:{_name}:{_id}>`"
        embed= discord.Embed(color= 0xee90ac, title= _name, description= f"`:{_name}:{_id}`\n[url]({_url})", timestamp= _timestamp)
        embed.set_image(url= _url)
        embed.set_footer(text= f"{footerText}|Added on ")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name= "figlet", description= "Render figlet fonts")
    @app_commands.describe(font= "Enter a valid figlet font")
    @app_commands.describe(text= "Enter what you want to said")
    async def __CMD_figlet(self, interaction: discord.Interaction, text: str, font: str= "small"):
        try:
            _render = nm.figlet(text, font)
        except:
            await interaction.response.send_message(
                    "This seems to not be a valid figlet font, please see http://www.figlet.org/examples.html",
                    ephemeral=True)
            return

        embed = discord.Embed(color= 0xee90ac, description= f"```\n{_render}\n```")
        await interaction.response.send_message(embed= embed)

    @app_commands.command(name= "reminder", description= "Reminds you to do a task after a certain ammount of time")
    @app_commands.describe(time= "Minutes till i remind you back")
    @app_commands.describe(task= "A task you want to be reminded of")
    async def __CMD_reminder(self, interaction: discord.Interaction, time: int, task: str):
        mins: int= time * 60
        fact= nekos.fact()
        await interaction.response.send_message(f"Alrighty!\nI'll remind you to **{task}**")
        await asyncio.sleep(mins)
        embed= discord.Embed(color= 0xee90ac, title= "Reminder", description= task)
        embed.set_footer(text= f'Want a fun fact? "{fact}"', icon_url= "http://nekomimi.tilde.team/Celestia/assets/__EMBED_fact.png")
        await interaction.user.send(embed= embed)

##############################################
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ToolCog(bot))
