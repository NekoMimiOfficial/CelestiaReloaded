import asyncio
import discord
from discord.ext import commands
from discord import app_commands

from Cogs.necho import cables as nek
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
        res= False
        await interaction.response.defer()
        while searching:
            res= nek.get_track(song, self.api)
            if res:
                break
            if retries < 1:
                await interaction.response.send_message("Maximum retries reached, API error", ephemeral= True)
                dprint(str(res), interaction)
                return
            retries= retries- 1
        dprint(res["url"], interaction)
        if interaction.user.voice:
            dprint("attempt play", interaction)
            if str(interaction.guild_id) in players:
                await interaction.response.send_message("I'm already playing a song in this guild!", ephemeral= True)
                return
            dprint("passed check", interaction)
            em0= discord.Embed(color= 0xEE90AC, title= f"Playing: {res['title']}")
            em0.set_footer(text= "Powered by Necho", icon_url="http://nekomimi.tilde.team/pool/05/nekoir.png")
            em0.add_field(name= "Duration", value= res["duration"], inline= True)
            em0.add_field(name= "Artist", value= res["artist"], inline= True)
            em0.add_field(name= "Album", value= res["album"], inline= True)
            em0.add_field(name= "Track ID", value= res["id"], inline= True)
            em0.set_thumbnail(url= res["cover"])
            dprint("embed created", interaction)
            await interaction.response.send_message(embed= em0)
            dprint("connecting", interaction)
            vc= interaction.user.voice.channel
            player= await vc.connect()
            players[str(interaction.guild_id)]= player
            dprint("playing", interaction)
            dprint("=====END=====", interaction)
            player.play(discord.FFmpegPCMAudio(source= res["url"]))
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
