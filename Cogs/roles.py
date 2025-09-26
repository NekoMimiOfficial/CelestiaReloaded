import discord
from discord.app_commands.models import app_command_option_factory
from discord.ext import commands
from discord import app_commands
import multiprocessing, time
import os, datetime

import Tools.DBCables as cables

sqldb= cables.Cables("celestia_datastore.db")
sqldb.connect()

def format_seconds(p: int):
    sec= p
    mins= 0
    hours= 0
    if sec >= 60:
        mins= int(sec/60)
    if mins >= 60:
        hours= int(mins/60)

    return f"{hours}:{mins%60}:{sec%60}"

class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot= bot;

    class UCSelect(discord.ui.Select):
        def __init__(self, uc):
            self.uc= uc
            options = []
            for entry in uc:
                options.append(discord.SelectOption(label= entry["role_name"], emoji= "📌"))
            
            super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            selected_option = self.values[0]
            aidee= 0
            for entry in self.uc:
                if entry["role_name"] == selected_option:
                    aidee= entry["role_id"]
            try:
                drole= interaction.guild.get_role(aidee)
                if drole:
                    toRemove= False
                    for role in interaction.user.roles:
                        if role.id == aidee:
                            toRemove= True
                    if toRemove:
                        await interaction.user.remove_roles(drole, reason= "User role de-assignment")
                        await interaction.response.send_message(f"You got rid of the {drole.mention} role!", ephemeral=True)
                        return
                    await interaction.user.add_roles(drole, reason= "User role assignment")
                    await interaction.response.send_message(f"You have acquired the {drole.mention} role!", ephemeral=True)
                else:
                    await interaction.response.send_message("An error occured, please report this to the devs")
            except Exception as e:
                await interaction.response.send_message(f"An error has occured, please contact a mod, error: {e}")

    class UCView(discord.ui.View):
        def __init__(self, uc):
            super().__init__(timeout= 300)
            self.add_item(RolesCog.UCSelect(uc))

    class UCRSelect(discord.ui.Select):
        def __init__(self, uc):
            self.uc= uc
            options = []
            for entry in uc:
                options.append(discord.SelectOption(label= entry["role_name"], emoji= "📌"))
            
            super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            selected_option = self.values[0]
            aidee= 0
            for entry in self.uc:
                if entry["role_name"] == selected_option:
                    break
                aidee= aidee+ 1

            self.uc.pop(aidee)
            new_uc= ""
            for entry in self.uc:
                new_uc= new_uc+ f"{entry['role_name']},{entry['role_id']};"
            new_uc= new_uc[:-1]
            sqldb.set_g_uc(interaction.guild_id, new_uc)
            await interaction.response.send_message(f"the role **{selected_option}** has been removed successfully", ephemeral= True)


    class UCRView(discord.ui.View):
        def __init__(self, uc):
            super().__init__(timeout= 300)
            self.add_item(RolesCog.UCRSelect(uc))

    role_commands= app_commands.Group(name= "roles", description= "Manage multiple role settings")

    @role_commands.command(name= "user-roles-remove-from-list", description= "Remove a role from the user role list")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def __CMD_role_menu_admin(self, interaction: discord.Interaction):
        registry= sqldb.get_g_uc(interaction.guild_id);
        if registry == "":
            setup= False;
        else:
            setup= True;

        if not setup:
            await interaction.response.send_message("[user-roles] the user role menu hasn't been setup for this guild", ephemeral= True);
            return;
        uc= []
        get_uc= registry
        for line in get_uc.split(";"):
            try:
                name, rid = line.strip().split(',')
                uc.append({'role_name': name, 'role_id': int(rid)})
            except ValueError:
                continue

        view = self.UCRView(uc)
        await interaction.response.send_message("Select role to remove:", view=view, ephemeral= True)


    @role_commands.command(name= "user-roles", description= "Allows users to assign themselves roles from a menu")
    @app_commands.guild_only()
    async def __CMD_role_menu_user(self, interaction: discord.Interaction):
        registry= sqldb.get_g_uc(interaction.guild_id)
        if registry == "":
            setup= False;
        else:
            setup= True;

        if not setup:
            await interaction.response.send_message("[user-roles] the user role menu hasn't been setup for this guild", ephemeral= True);
            return;
        uc= []
        get_uc= registry
        for line in get_uc.split(";"):
            try:
                name, rid = line.strip().split(',')
                uc.append({'role_name': name, 'role_id': int(rid)})
            except ValueError:
                continue

        view = self.UCView(uc)
        await interaction.response.send_message("Select role to assign:", view=view, ephemeral= True)

    @role_commands.command(name= "user-roles-add-to-list", description= "Adds a new role to the user roles list")
    @app_commands.describe(role= "Role to add to the list.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def __CMD_join_role_add(self, interaction: discord.Interaction, role: discord.Role):
        uc= []
        get_uc= sqldb.get_g_uc(interaction.guild_id)
        for line in get_uc.split(";"):
            try:
                name, rid= line.strip().split(',')
                uc.append({'role_name': name, 'role_id': int(rid)})
            except ValueError:
                continue

        uc.append({'role_name': role.name, 'role_id': role.id})
        new_uc= ""
        for entry in uc:
            new_uc= new_uc+ f"{entry['role_name']},{entry['role_id']};"
        new_uc= new_uc[:-1]
        sqldb.set_g_uc(interaction.guild_id, new_uc)
        await interaction.response.send_message(f"Done! the role {role.mention} has now been added to the user roles", ephemeral= True)

    @role_commands.command(name= "join-role", description= "Sets a role that all users that may join will get")
    @app_commands.describe(role= "The role to use for the join role")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles= True)
    async def __CMD_join_role(self, interaction: discord.Interaction, role: discord.Role):
        sqldb.set_g_jr(interaction.guild_id, role.id)
        await interaction.response.send_message(f"`{role.name}` has been set as the join role")

    @role_commands.command(name= "remove-join-role", description= "Removes the join role")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles= True)
    async def __CMD_join_role(self, interaction: discord.Interaction):
        sqldb.set_g_jr(interaction.guild_id, 0)
        await interaction.response.send_message(f"Join role disabled.")

    @role_commands.command(name= "user-verify-welcome-message", description= "Sets the welcome message that a user gets after a successful verification")
    @app_commands.describe(message= "The message to send to the user once verification is complete. use [user] or [guild] to mention the user or guild.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def __CMD_verity_welcome(self, interaction: discord.Interaction, message: str):
        message= message
        if message == "":
            message= "Yay! Welcome, [user]! So happy you're here. Don't be shy, come say hi and make yourself at home!"
        sqldb.set_g_welcome(interaction.guild_id, message)
        await interaction.response.send_message("Done!\nI will now greet your members with the following message apon verification\n"+message, ephemeral= True)

    @role_commands.command(name= "user-verify", description= "A tool to grant users a role when they manage to verify successfully.")
    @app_commands.guild_only()
    @app_commands.describe(message= "The message which you want to display on the verifier, use the following phrases to add some dynamic text, [guild] for guild name, [owner] for owner mention, [role] for role mention, <br> for a new line")
    @app_commands.checks.has_permissions(administrator= True)
    @app_commands.describe(verifygrantrole= "The role to grant members who succeed in the verification.")
    async def __CMD_verity_cs(self, interaction: discord.Interaction, verifygrantrole: discord.Role, message: str= None):
        default_msg= f"Welcome to **{interaction.guild.name}**!\nPlease verify yourself to get access to the {verifygrantrole.mention} role."
        message= message or default_msg
        message= message.replace("[guild]", interaction.guild.name)
        message= message.replace("[role]", verifygrantrole.mention)
        message= message.replace("[owner]", interaction.guild.owner.mention)
        message= message.replace("<br>", "\n")
        sqldb.set_g_verity(interaction.guild_id, verifygrantrole.id)
        await interaction.channel.send(f"✿  {message}", allowed_mentions= discord.AllowedMentions.none(), view= self.Verifier())
        await interaction.response.send_message("❀  Done, you may now rest peacefully knowing no bots will join :3", ephemeral= True)

    @role_commands.command(name= "kick-timeout", description= "Sets the time in seconds to wait before kicking the user if they did not verify yet")
    @app_commands.guild_only()
    @app_commands.describe(wait= "Time to wait before kicking (in seconds)")
    @app_commands.checks.has_permissions(administrator= True)
    async def __CMD_verity_drm(self, interaction: discord.Interaction, wait: int= 86400):
        sqldb.set_g_drm(interaction.guild_id, wait)
        await interaction.response.send_message(f"Updated timeout to `{format_seconds(wait)}`", ephemeral= True)


    class VerificationButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label= "Verify", style= discord.ButtonStyle.green, custom_id= "CelestiaVerifyService")

        def get_log_channel(self, gid: int): # tuple(int, bool)
            log_c= sqldb.get_g_mod(gid)
            log_b= sqldb.get_g_bot(gid)
            return (log_c, log_b)

        def check_log_channel(self, gid: int)-> bool:
            return sqldb.chk_g_mod(gid)

        async def callback(self, interaction: discord.Interaction):
            roleID= int(sqldb.get_g_verity(interaction.guild_id))
            welcome_msg= sqldb.get_g_welcome(interaction.guild_id)
            if welcome_msg == "":
                welcome_msg= "Yay! Welcome, [user]! So happy you're here. Don't be shy, come say hi and make yourself at home!"

            welcome_msg= welcome_msg.replace("[user]", interaction.user.display_name)
            welcome_msg= welcome_msg.replace("[guild]", interaction.guild.name)
            role= interaction.guild.get_role(roleID)
            if role in interaction.user.roles:
                await interaction.response.defer()
                return
            if role:
                await interaction.user.add_roles(role, reason= "Verified successfully")

                try:
                    logchnlid, _= self.get_log_channel(interaction.guild_id)
                    logging= interaction.guild.get_channel(logchnlid)
                    verbed= discord.Embed(color= 0xa6d189, title= f"Member passed verification!", description= f"The member {interaction.user.mention} has successfully managed to complete the verification and has obtained the {role.mention} role!")
                    if interaction.user.display_avatar:
                        verbed.set_thumbnail(url=interaction.user.display_avatar)

                    verbed.add_field(name="Full name", value=interaction.user.global_name, inline=True)
                    verbed.add_field(name="Nickname", value=interaction.user.nick if hasattr(interaction.user, "nick") else "None", inline=True)
                    verbed.add_field(name= "UID", value= interaction.user.id)
                    verbed.add_field(name= "SID", value= interaction.user.name)
                    verbed.add_field(name="Account created", value=interaction.user.created_at.date(), inline=True)
                    verbed.add_field(name="Joined this server", value=interaction.user.joined_at.date(), inline=True)
                    verbed.timestamp= datetime.datetime.now(datetime.timezone.utc)

                    await logging.send(embed= verbed)
                except:
                    pass
                await interaction.response.send_message(f"❀  {welcome_msg}", ephemeral= True)
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

    def auto_clean(self, member: discord.Member, role: int):
        if sqldb.get_g_verity(member.guild.id) == 0:
            return

        g_role= member.guild.get_role(role)
        if not g_role:
            return

        time.sleep(int(sqldb.get_g_drm(member.guild.id)))
        member_n= member.guild.get_member(member.id)
        if member_n:
            member= member_n

        if not g_role in member.roles:
            await member.kick(reason= "Member did not verify within 24 hours")
            em0= discord.Embed(title= "Member did not verify within 24 hours", color= 0x81C8BE, description= f"The user {member.mention} was kicked after not verifying within the verification period")

            if member.display_avatar:
                em0.set_thumbnail(url= member.display_avatar)

            em0.add_field(name="Full name", value=member.global_name, inline=True)
            em0.add_field(name="Nickname", value=member.nick if hasattr(member, "nick") else "None", inline=True)
            em0.add_field(name= "UID", value= member.id)
            em0.add_field(name= "SID", value= member.name)
            em0.add_field(name="Account created", value=member.created_at.date(), inline=True)
            em0.add_field(name="Joined this server", value=member.joined_at.date(), inline=True)
            em0.timestamp= datetime.datetime.now(datetime.timezone.utc)

            await member.guild.get_channel(int(sqldb.get_g_mod(member.guild.id))).send(embed= em0)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            rid= int(sqldb.get_g_mod(member.guild.id))
            role= member.guild.get_role(rid)
            if role:
                await member.add_roles(role, reason="Join role assigned")
                
            proc= multiprocessing.Process(target= self.auto_clean, args= (member, int(sqldb.get_g_verity(member.guild.id))))
            proc.run()



async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(RolesCog(bot));
