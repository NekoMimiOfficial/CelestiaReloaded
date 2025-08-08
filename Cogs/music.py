import asyncio
import discord
from discord.ext import commands
from discord import app_commands

from Cogs.Nekoir import PYAAPI as nek
from NekoMimi import reg

players= {}
def dprint(msg, intr: discord.Interaction):
    print(f"[Music Cog] @{intr.created_at} [{intr.guild_id}@{intr.guild.name}] [{intr.user.id}@{intr.user.display_name}] {msg}")

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot
        self.api= reg.readCell("nekoir")

    @app_commands.command(name= "play", description= "Play a song")
    @app_commands.describe(song= "Song name")
    @app_commands.guild_only()
    async def __cmd_play(self, interaction: discord.Interaction, song: str):
        searching= True
        retries= 30
        while searching:
            try:
                fapi= nek.ApiService(self.api)
                tapi= fapi.search(song, nek.SearchType.TRACK)[0]
                sapi= fapi.track(tapi["id"], "LOW")
                url= sapi["urls"][0]
                searching= False
                break
            except Exception as e:
                dprint(f"Nekoir API error: {e}", interaction)
            if retries < 1:
                break
            retries = retries - 1
        dprint(url, interaction)
        # dprint(tapi, interaction)
        if interaction.user.voice:
            dprint("attempting to play", interaction)
            if str(interaction.guild_id) in players:
                await interaction.response.send_message("I'm already playing a song in this guild!", ephemeral= True)
                return
            dprint("passed check", interaction)
            em0= discord.Embed(color= 0xEE90AC, title= f"Playing: {tapi['title']}")
            dprint("embed init", interaction)
            em0.set_footer(text= "Powered by Nekoir", icon_url="http://nekomimi.tilde.team/pool/05/nekoir.png")
            dprint("embed footer", interaction)
            em0.add_field(name= "Duration", value= tapi["duration"], inline= True)
            dprint("embed dur", interaction)
            em0.add_field(name= "Track ID", value= tapi["id"], inline= True)
            dprint("embed tid", interaction)
            em0.set_thumbnail(url= tapi["cover"])
            dprint("embed cov", interaction)
            await interaction.response.send_message(embed= em0)
            dprint("connecting", interaction)
            vc= interaction.user.voice.channel
            player= await vc.connect()
            players[str(interaction.guild_id)]= player
            dprint("playing", interaction)
            dprint("==========================================", interaction)
            player.play(discord.FFmpegPCMAudio(source= url))
            while player.is_playing():
                await asyncio.sleep(1)
            await player.disconnect()
            del players[str(interaction.guild_id)]
        else:
            await interaction.response.send_message("You must connect to a VC first...", ephemeral= True)

    @app_commands.command(name= "stop", description= "Stop a song")
    @app_commands.guild_only()
    async def __cmd_stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await players[str(interaction.guild_id)].stop()
            await interaction.guild.voice_client.disconnect(force= True)
            del players[str(interaction.guild_id)]
            await interaction.response.send_message("Stopped playing.")
        else:
            await interaction.response.send_message("But it wasn't even playing...", ephemeral= True)

    @app_commands.command(name= "resume", description= "Resumes a song")
    @app_commands.guild_only()
    async def __cmd_resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            if players[str(interaction.guild_id)].is_paused():
                await players[str(interaction.guild_id)].stop()
                await interaction.response.send_message("Resumed playing.")
            else:
                await interaction.response.send_message("But it was playing all along...", ephemeral= True)
        else:
            await interaction.response.send_message("But it wasn't even playing...", ephemeral= True)

    @app_commands.command(name= "pause", description= "Pauses a song")
    @app_commands.guild_only()
    async def __cmd_pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            if players[str(interaction.guild_id)].is_playing():
                await players[str(interaction.guild_id)].stop()
                await interaction.response.send_message("Paused playing.")
            else:
                await interaction.response.send_message("But it was paused all along...", ephemeral= True)
        else:
            await interaction.response.send_message("But it wasn't even playing...", ephemeral= True)


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
