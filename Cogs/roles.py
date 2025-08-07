import discord
from discord.ext import commands
from discord import app_commands

from NekoMimi import reg as nreg

class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        bot= bot;

    role_commands= app_commands.Group(name= "roles", description= "Manage multiple role settings")

    @role_commands.command(name= "user-roles", description= "Allows users to assign themselves roles from a menu")
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

    @role_commands.command(name= "join-role", description= "Sets a role that all users that may join will get")
    @app_commands.describe(role= "The role to use for the join role")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles= True)
    async def __CMD_join_role(self, interaction: discord.Interaction, role: discord.Role):
        regName= "Celestia-Guilds-"+str(interaction.guild_id)
        rid= str(role.id)
        db= nreg.Database(regName)
        db.store("join-role", rid+":")
        await interaction.response.send_message(f"`{role.name}` has been set as the join role")

    @role_commands.command(name= "remove-join-role", description= "Removes the join role")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles= True)
    async def __CMD_join_role(self, interaction: discord.Interaction):
        regName= "Celestia-Guilds-"+str(interaction.guild_id)
        db= nreg.Database(regName)
        db.store("join-role", "0:")
        await interaction.response.send_message(f"Join role disabled.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            regName= "Celestia-Guilds-"+str(member.guild.id)
            db= nreg.Database(regName)
            rid= int(db.query("join-role").split(":")[0])
            role= member.guild.get_role(rid)
            if role:
                await member.add_roles(role, reason="Join role assigned")


async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(RolesCog(bot));
