import discord
from discord import app_commands
from discord.ext import commands

import pyttsx3
import asyncio
import os

class TTSCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
        self.engine= pyttsx3.init()
##############################################

    @app_commands.command(name= "tts", description= "play a tts into a vc from a message")
    @app_commands.describe(text= "the text to be TTS-ed")
    async def com_tts(self, interaction: discord.Interaction, text:str):
        file= str(interaction.user.id)+ "-tts.mp3"
        self.engine.save_to_file(text, file)
        await asyncio.to_thread(self.engine.runAndWait)

        await interaction.response.defer()
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You're not in a VC", ephemeral= True)
            return

        vc= interaction.user.voice.channel
        player= await vc.connect()
        player.play(discord.FFmpegPCMAudio(source= file, options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'))
        os.remove(file)

##############################################
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TTSCog(bot))
