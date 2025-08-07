import discord
import asyncio
from discord import app_commands
from discord.ext import commands

from NekoMimi import utils as nm
from NekoMimi import reg as nreg

class modal_interface(discord.ui.Modal, title= "Site Address"):
    site= discord.ui.TextInput(label= "Site", placeholder= "http://site.example.com");

    async def on_submit(self, interaction: discord.Interaction):
        embed_interfact= discord.Embed(description= "starting service...");
        _uri_state= True;
        _uri= self.site.value;
        if " " in self.site.value:
            _uri_state= False;
        if not self.site.value.startswith("http"):
            _uri= "http://"+_uri;
        if not "://" in self.site.value:
            _uri_state= False;

        if not _uri_state:
            await interaction.response.send_message(
                    "[uptime] incorrecly formatted site url, please make sure your url is formatted as follows: `http://site.example.com`",
                    ephemeral= True);
            return

        await interaction.response.send_message("[uptime] running uptime", ephemeral= True);
        main_counter_interface= await interaction.channel.send(embed= embed_interfact);
        await asyncio.sleep(1)
        await main_counter_interface.edit(content= "hello")

class UptimeCog(commands.Cog):
    def __init__(self, bot: commands.Bot)-> None:
        self.bot= bot;

#~~[Code section]~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator= True)
    @app_commands.command(name="uptime", description="An uptime monitor for a website")
    async def __CMD_uptime(self, interaction: discord.Interaction):
        await interaction.response.send_modal(modal_interface());

#~~[End of code section]~~~~~~~~~~~~~~~~~~~~~~~~~~~

async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(UptimeCog(bot));
