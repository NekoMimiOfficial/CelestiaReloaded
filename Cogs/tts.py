import discord
from discord import app_commands
from discord.ext import commands


from google import genai
from google.genai import types
import wave
import os

from NekoMimi import reg
import asyncio

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

class TTSCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
        self.client = genai.Client(api_key= reg.readCell("elGoog"))
##############################################

    @app_commands.command(name= "tts", description= "play a tts into a vc from a message")
    @app_commands.describe(text= "the text to be TTS-ed")
    async def com_tts(self, interaction: discord.Interaction, text:str):
        file= str(interaction.user.id)+ "-tts.mp3"
        response = self.client.models.generate_content(
           model="gemini-3.1-flash-tts-preview",
           contents=f"Say cheerfully: {text}",
           config=types.GenerateContentConfig(
              response_modalities=["AUDIO"],
              speech_config=types.SpeechConfig(
                 voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                       voice_name='Kore',
                    )
                 )
              ),
           )
        )

        data = response.candidates[0].content.parts[0].inline_data.data

        wave_file(file, data)

        await interaction.response.defer()
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You're not in a VC", ephemeral= True)
            return

        vc= interaction.user.voice.channel
        player= await vc.connect()
        player.play(discord.FFmpegPCMAudio(source= file))
        await asyncio.sleep(2)
        os.remove(file)

##############################################
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TTSCog(bot))
