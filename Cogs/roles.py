import discord
from discord.ext import commands
from discord import app_commands

from NekoMimi import reg as nreg

class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot= bot;

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

    @role_commands.command(name= "user-verify", description= "A tool to grant users a role when they manage to verify successfully.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    @app_commands.describe(verifygrantrole= "The role to grant members who succeed in the verification.")
    async def __CMD_verity_cs(self, interaction: discord.Interaction, verifygrantrole: discord.Role):
        db= nreg.Database(f"Celestia-Guilds-{interaction.guild_id}")
        db.store("verity-cs", str(verifygrantrole.id))
        await interaction.response.send_message("❀  Done, you may now rest peacefully knowing no bots will join :3", ephemeral= True)
        await interaction.channel.send(f"✿  Welcome to **{interaction.guild.name}**!\nPlease verify yourself to get access to the {verifygrantrole.mention} role.", allowed_mentions= discord.AllowedMentions.none(), view= self.Verifier())


    class VerificationButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label= "Verify", style= discord.ButtonStyle.green, custom_id= "CelestiaVerifyService")

        async def callback(self, interaction: discord.Interaction):
            db= nreg.Database(f"Celestia-Guilds-{interaction.guild_id}")
            print("start operation")
            roleID= int(db.query("verity-cs"))
            print("get RID")
            role= interaction.guild.get_role(roleID)
            print("get Role")
            if role:
                try:
                    await interaction.user.add_roles(role, reason= "Verified successfully")
                    print("assign Role")
                except Exception as e:
                    await interaction.response.send_message(f"Internal error: {e}\n\nPlease report this to the devs")
                await interaction.response.send_message("❀  Access granted!\nHave a safe stay :pink_heart:", ephemeral= True)
            else:
                await interaction.response.send_message("❀  Error granting role!\nPlease report this to the admins", ephemeral= True)

    class Verifier(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(RolesCog.VerificationButton())

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.add_view(self.Verifier())
            print("[  ok  ] attaching Verifier view")
        except Exception as e:
            print(f"[ fail ] attaching Verifier: {e}")

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
