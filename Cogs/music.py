import asyncio
import math, time
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from Cogs.necho import cables as nek
from NekoMimi import reg

def dprint(msg, intr: discord.Interaction):
    print(f"[Music Cog] @{intr.created_at} [{intr.guild_id}@{intr.guild.name}] [{intr.user.id}@{intr.user.display_name}] {msg}")

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot
        self.api= reg.readCell("nekoir")
        self.players= {}

    def parse_duration(self, duration_str: str) -> Optional[int]:
        if duration_str == "Unknown":
            return None
        try:
            parts = list(map(int, duration_str.split(':')))

            if len(parts) == 1:
                return parts[0]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            return None
        except ValueError:
            return None

    def format_time(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02}:{secs:02}"
        return f"{minutes:02}:{secs:02}"

    def create_progress_bar(self, current_time: int, total_duration: int, steps: int = 20) -> str:
        if total_duration <= 0:
            return "`0:00 [                    ] 0:00`"

        progress_ratio = current_time / total_duration
        filled_steps = math.ceil(progress_ratio * steps)
        empty_steps = steps - filled_steps

        bar = f"[{'/' * filled_steps}{' ' * empty_steps}]"

        current_time_str = self.format_time(current_time)
        total_duration_str = self.format_time(total_duration)

        return f"`{current_time_str} {bar} {total_duration_str}`"

    async def update_progress_task(self, interaction: discord.Interaction, message: discord.Message, player: discord.VoiceClient, total_duration_sec: int, initial_embed: discord.Embed):
        start_time = time.time()
        update_interval = 5
        progress_field_name = "Progress"
        original_embed = initial_embed.copy()

        try:
            while player.is_playing():
                original_embed = initial_embed.copy()
                elapsed_time = int(time.time() - start_time)

                if elapsed_time > total_duration_sec:
                    elapsed_time = total_duration_sec

                progress_bar = self.create_progress_bar(elapsed_time, total_duration_sec)
                new_embed = original_embed.copy()
                i= 0
                for fiels in new_embed.fields:
                    if fiels.name and "progress" in fiels.name.lower():
                        new_embed.remove_field(i)
                        i= i- 1
                    i= i+ 1

                new_embed.add_field(
                    name=progress_field_name,
                    value=progress_bar,
                    inline=False
                )

                await message.edit(embed=new_embed)
                await asyncio.sleep(update_interval)

            final_bar = self.create_progress_bar(total_duration_sec, total_duration_sec)

            final_embed = original_embed.copy()
            i= 0
            for fiels in final_embed.fields:
                if fiels.name and "progress" in fiels.name.lower():
                    final_embed.remove_field(i)
                    i= i- 1
                i= i+ 1

            final_embed.add_field(
                name=progress_field_name,
                value=final_bar + " **[FINISHED]**",
                inline=False
            )
            await message.edit(embed=final_embed)


        except discord.errors.NotFound:
            dprint("Progress task failed: Message not found.", interaction)
        except Exception as e:
            dprint(f"Error in progress task: {e}", interaction)
        finally:
            if player:
                dprint("Disconnecting voice client in cleanup.", interaction)
                await asyncio.sleep(1)
                if player.is_connected():
                    await player.disconnect()
                guild_id_str = str(interaction.guild_id)
                if guild_id_str in self.players:
                    del self.players[guild_id_str]

            dprint("Playback finished and progress task terminated.", interaction)

    @app_commands.command(name= "play", description= "Play a song")
    @app_commands.describe(song= "Song name")
    @app_commands.guild_only()
    async def __cmd_play(self, interaction: discord.Interaction, song: str):
        searching= True
        retries= 30
        res= False

        await interaction.response.defer()
        if not song.startswith("http://") and not song.startswith("https://") and not song.count(".") > 0:
            while searching:
                res= await nek.get_track(song, self.api)
                if res:
                    break
                if retries < 1:
                    await interaction.followup.send("Maximum retries reached, API error", ephemeral= True)
                    dprint(str(res), interaction)
                    return
                retries = retries - 1
            dprint(res["url"], interaction)
        else:
            res= {
                'url': song,
                'title': "Remote media",
                'artist': "Unknown",
                'album': "Unknown",
                'duration': "Unknown",
                'id': "None",
                'cover': "http://nekomimi.tilde.team/pool/05/missingno.png"
            }

        if interaction.user.voice and interaction.user.voice.channel:
            dprint("attempt play", interaction)
            guild_id_str = str(interaction.guild_id)

            if guild_id_str in self.players and self.players[guild_id_str].is_playing():
                await interaction.followup.send("I'm already playing a song in this guild!", ephemeral= True)
                return

            dprint("passed check", interaction)

            em0= discord.Embed(color= 0xEE90AC, title= f"Playing: {res['title']}")
            em0.set_footer(text= "Powered by Nekoir3 core", icon_url="http://nekomimi.tilde.team/pool/05/nekoir.png")
            em0.add_field(name= "Duration", value= res["duration"], inline= True)
            em0.add_field(name= "Artist", value= res["artist"], inline= True)
            em0.add_field(name= "Album", value= res["album"], inline= True)
            em0.add_field(name= "Track ID", value= res["id"], inline= True)
            em0.set_thumbnail(url= res["cover"])
            dprint("embed created", interaction)

            message = await interaction.followup.send(embed= em0)
            dprint("connecting", interaction)
            vc = interaction.user.voice.channel
            player = None

            try:
                if guild_id_str in self.players:
                    player = self.players[guild_id_str]
                    await player.move_to(vc)
                else:
                    if not interaction.guild.voice_client:
                        player = await vc.connect()
                    self.players[guild_id_str] = player

            except Exception as e:
                dprint(f"Voice Connection/Move Error: {e}", interaction)
                await interaction.followup.send("Failed to connect to the voice channel due to a network or connection error. Please try again.", ephemeral=True)
                return

            dprint("playing", interaction)
            player.play(discord.FFmpegPCMAudio(source= res["url"], options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'))

            total_duration_sec = self.parse_duration(res["duration"])
            if total_duration_sec is not None:
                dprint(f"Starting progress task for {total_duration_sec} seconds.", interaction)

                asyncio.create_task(
                    self.update_progress_task(interaction, message, player, total_duration_sec, em0)
                )
            else:
                dprint("Duration unknown, skipping progress bar.", interaction)

            dprint("=====CMD END=====", interaction)

        else:
            await interaction.followup.send("You must connect to a VC first...", ephemeral= True)

    @app_commands.command(name= "stop", description= "Stop a song")
    @app_commands.guild_only()
    async def __cmd_stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            try:
                await interaction.guild.voice_client.disconnect(force= True)
                if str(interaction.guild_id) in self.players:
                    await self.players[str(interaction.guild_id)].stop()
                    del self.players[str(interaction.guild_id)]
            except:
                pass
            await interaction.response.send_message("Stopped playing.")
        else:
            await interaction.response.send_message("But it wasn't even playing...", ephemeral= True)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
