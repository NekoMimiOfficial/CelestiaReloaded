import discord
from discord.ext import commands
from discord import app_commands

class ServerConfView(discord.ui.View):
    def __init__(self):
        super().__init__();

    @discord.ui.button(label= "Stop uptime", style= discord.ButtonStyle.red)
    async def __VIEW_stop_uptime(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("[uptime] stopped uptime command", ephemeral= True);
        self.stop();

async def _server_conf_runner(interaction: discord.Interaction):
    _sc_view= ServerConfView();
    await interaction.response.send_message(view= _sc_view);

class Dropdown(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label='Mass Mod Tools', description='Advanced moderation'),
            discord.SelectOption(label='Server Configuration', description='Specific server settings and tools'),
            discord.SelectOption(label='Game Configuration', description='Configure the game instance on your server'),
        ]

        super().__init__(placeholder='Choose your action...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Server Configuration":
            await _server_conf_runner(interaction);

class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__();
        self.add_item(Dropdown());

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot= bot;

#~~[Code section]~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator= True)
    @app_commands.command(name= "server-panel", description= "The adminstrative panel for quick actions on this server")
    async def __CMD_mod_panel(self, interaction: discord.Interaction):
        pview= PanelView();
        await interaction.response.send_message(view= pview);

#~~[End of code section]~~~~~~~~~~~~~~~~~~~~~~

async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(AdminCog(bot));
