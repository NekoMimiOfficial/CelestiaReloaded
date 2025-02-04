import discord
from discord.ext import commands
from discord import app_commands

from NekoMimi import reg as nreg

class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        bot= bot;

    @app_commands.command(name= "user-roles", description= "A role picker")
    async def __CMD_role_menu_user(self, interaction: discord.Interaction):
        registryName= "Celestia-Guilds-"+str(interaction.guild_id);
        registry= nreg.Database(registryName);
        if registry.query("uc-rolemenu") == "":
            setup= False;
        else:
            setup= True;

        if not setup:
            await interaction.response.send_message("[user-roles] the user role menu hasn't been setup for this guild", ephemeral= True);
            return;

        items= registry.query("uc-rolemenu");
        #<start>[role-name](role-id):[role-name](role-id)<end>
        corrupted_database= False;
        if not items.startswith("<start>"):
            corrupted_database= True;
        if not items.endswith("<end>"):
            corrupted_database= True;
        if not len(items.split("["))-1 == len(items.split(":")):
            corrupted_database= True;
        if not len(items.split(")"))-1 == len(items.split(":")):
            corrupted_database= True;
        
        if corrupted_database:
            await interaction.channel.send("[user-roles] database malformed, please ask an admin to reset the menu\nsending bug report...");
            #add reporting
            return;

async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(RolesCog(bot));
