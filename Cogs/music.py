import asyncio
import discord
from discord.ext import commands
from discord import app_commands

from Cogs.Nekoir import PYAAPI as nek
from NekoMimi import reg

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot
        self.api= reg.readCell("nekoir")

    @app_commands.command(name= "play", description= "Play a song")
    @app_commands.describe(song= "Song name")
    @app_commands.guild_only()
    async def __cmd_play(self, interaction: discord.Interaction, song: str):
        searching= True
        while searching:
            try:
                fapi= nek.ApiService(self.api)
                tapi= fapi.search(song, nek.SearchType.TRACK)[0]
                sapi= fapi.track(tapi["id"], "LOW")
                url= sapi["urls"][0]
                searching= False
                break
            except Exception as e:
                print(f"Nekoir API error: {e}")
                continue
        print(url)
        if interaction.user.voice:
            await interaction.response.send_message(f"Playing **{tapi['title']}**!")
            vc= interaction.user.voice.channel
            player= await vc.connect()
            player.play(discord.FFmpegPCMAudio(source= url))
            while player.is_playing():
                await asyncio.sleep(1)
            await player.disconnect()
        else:
            await interaction.response.send_message("You must connect to a VC first...", ephemeral= True)

    @app_commands.command(name= "stop", description= "Stop a song")
    @app_commands.guild_only()
    async def __cmd_stop(self, interaction: discord.Interaction):
        if self.bot.voice:
            await self.bot.voice.channel.disconnect()
            await interaction.response.send_message("Stopped playing.")
        else:
            await interaction.response.send_message("But it wasn't even playing...", ephemeral= True)



async def setup(bot):
    await bot.add_cog(MusicCog(bot))
