from datetime import date, time
import datetime
import discord
from discord.ext import commands
from discord import app_commands, role
import os.path

import Tools.DBCables as cables

sqldb= cables.Cables("celestia_datastore.db")

class logger(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    def fixEdit(self,text):
        cleanOutYay = ''
        splitLine = text.split("`")
        for line in splitLine:
            cleanOutYay = cleanOutYay + line
        return cleanOutYay

    def checkEdit(self,before,after):
        if before == after:
            return False
        else:
            return True

    async def create_log_channel(self, gid: int, cid: int):
        await sqldb.connect()
        await sqldb.set_g_mod(gid, cid)
        await sqldb.set_g_bot(gid, await sqldb.get_g_mod(gid))

    async def rm_log_channel(self, gid: int)-> str:
        await sqldb.connect()
        chk= await sqldb.chk_g_mod(gid)
        if not chk:
            return "This server isn't registered in the modlog system..."
        await sqldb.set_g_mod(gid, 0)
        return "This server is now registered in the modlog system."

    async def botToggle(self, gid: int, toggle: bool)-> str:
        await sqldb.connect()
        bot= 0
        if toggle:
            bot= 1
        await sqldb.set_g_bot(gid, bot)
        if bot == 0:
            return "Successfully removed bots from the modlog!"
        return "Successfully enabled bot monitoring in modlog!"

    async def get_log_channel(self, gid: int): # tuple(int, bool)
        await sqldb.connect()
        log_c= await sqldb.get_g_mod(gid)
        log_b= await sqldb.get_g_bot(gid)
        return (log_c, log_b)

    async def check_log_channel(self, gid: int)-> bool:
        await sqldb.connect()
        res= await sqldb.chk_g_mod(gid)
        return res

    logging= app_commands.Group(name= "logging", description= "Mod log tools")

    @logging.command(name= "setup", description= "setup the modlog")
    @app_commands.describe(chnl= "Channel to bind the logs to")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def modlogsetup(self, interaction: discord.Interaction, chnl:discord.TextChannel):
        channel = chnl.id
        guild = interaction.guild_id
        await self.create_log_channel(guild,channel)
        await interaction.response.send_message(f"Bound logs to channel `{chnl.name}` !")

    @logging.command(name= "disable", description= "disable the modlog")
    @commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def removemodlog(self, interaction: discord.Interaction):
        guild = interaction.guild_id
        work = await self.rm_log_channel(guild)
        await interaction.response.send_message(work)

    @logging.command(name= "monitor-bots", description= "Sets whether you want to monitor bot messages")
    @app_commands.describe(toggle= "True for enabling bot monitoring, False otherwise")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def monbot(self, interaction: discord.Interaction, toggle: bool):
        guild= interaction.guild_id
        resp= await self.botToggle(guild, toggle)
        embed= discord.Embed(color= 0xEE90AC, description=resp)
        await interaction.response.send_message(embed= embed, ephemeral= True)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        if not await self.check_log_channel(role.guild.id):
            return
        logchnl, _= await self.get_log_channel(role.guild.id)
        embed= discord.Embed(color= 0xb7bdf8, title= "Role Created")
        embed.add_field(name= "Role name", value= role.name, inline= True)
        embed.add_field(name= "Role color", value= role.color, inline= True)
        embed.add_field(name= "Created at", value= role.created_at.date(), inline= True)
        embed.add_field(name= "Permissions", value= str(role.permissions.value), inline= False)
        embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
        await self.bot.get_channel(logchnl).send(embed= embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, roleO: discord.Role, roleN: discord.Role):
        if not await self.check_log_channel(roleO.guild.id):
            return
        if roleO.name == roleN.name and roleO.color == roleN.color and roleO.permissions == roleN.permissions:
            return
        logchnl, _= await self.get_log_channel(roleO.guild.id)
        if roleO.name == roleN.name:
            rname= roleO.name
        else:
            rname= f"{roleN.name} (old: {roleO.name})"

        if roleO.color == roleN.color:
            rcol= roleO.color
        else:
            rcol= f"{roleN.color} (old: {roleO.color})"
        embed= discord.Embed(color= 0x8aadf4, title= "Role Updated")
        embed.add_field(name= "Role name", value= rname, inline= True)
        embed.add_field(name= "Role color", value= rcol, inline= True)
        embed.add_field(name= "Created at", value= roleO.created_at.date(), inline= True)
        embed.add_field(name= "Permissions", value= str(roleN.permissions.value), inline= False)
        embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
        await self.bot.get_channel(logchnl).send(embed= embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        if not await self.check_log_channel(role.guild.id):
            return
        logchnl, _= await self.get_log_channel(role.guild.id)
        embed= discord.Embed(color= 0xc6a0f6, title= "Role Deleted")
        embed.add_field(name= "Role name", value= role.name, inline= True)
        embed.add_field(name= "Role color", value= role.color, inline= True)
        embed.add_field(name= "Created at", value= role.created_at.date(), inline= True)
        embed.add_field(name= "Permissions", value= str(role.permissions.value), inline= False)
        embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
        await self.bot.get_channel(logchnl).send(embed= embed)

    @commands.Cog.listener()
    async def on_message_delete(self,message: discord.Message):
        if not message.author.id == self.bot.user.id: #Checks the ID, if AuthorID = BotID, return. Else, continue.
            guild = message.guild.id
            chk = await self.check_log_channel(guild)
            if message == '':
                emp = False
            else:
                emp = True
            if chk == True and emp == True:
                author = message.author #Defines the message author
                content = message.content #Defines the message content
                channel = message.channel #Defines the message channel
                logchnl, botAllow = await self.get_log_channel(guild)
                logchannel = self.bot.get_channel(logchnl)
                if author.bot:
                    if not botAllow:
                        return
                embed = discord.Embed(color=0xf5bde6,title="Message Deleted",description=f"A message by {author.mention} was deleted in {channel.mention}")
                embed.add_field(name= "Message Deleted", value= f"```\n{content}\n```")
                if author.avatar.url:
                    embed.set_thumbnail(url=author.avatar.url)
                embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
                await logchannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self,before,after: discord.Message):
        if not before.author.id == self.bot.user.id: #Checks the ID, if AuthorID = BotID, return. Else, continue.
            guild = before.guild.id
            chk = await self.check_log_channel(guild)
            if chk == True:
                author = before.author #Defines the message author
                contentB = before.content #Defines the message content
                contentA = after.content #Defines the message content
                contentB = self.fixEdit(contentB)
                contentA = self.fixEdit(contentA)
                channel = before.channel #Defines the message channel
                logchnl, botAllow = await self.get_log_channel(guild)
                logchannel = self.bot.get_channel(logchnl)
                if author.bot:
                    if not botAllow:
                        return
                embed = discord.Embed(color=0xeed49f,title="Message Edited",description=f"A [message]({after.jump_url}) by {author.mention} was edited in {channel.mention}")
                embed.add_field(name= "From", value= f"```\n{contentB}\n```", inline= True)
                embed.add_field(name= "After", value= f"```\n{contentA}\n```", inline= True)
                embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
                if author.avatar.url:
                    embed.set_thumbnail(url=author.avatar.url)
                chk = self.checkEdit(contentB,contentA)
                if chk == True:
                    await logchannel.send(embed=embed)
                else:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self,member: discord.Member):
        guild = member.guild.id
        chk = await self.check_log_channel(guild)
        if chk == True:
            logchnl, _ = await self.get_log_channel(guild)
            logchannel = self.bot.get_channel(logchnl)
            embed = discord.Embed(color=0xa6da95,title="Member Joined",description=f"Member {member.mention} has joined the server !")

            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar)

            embed.add_field(name="Full name", value=member.global_name, inline=True)
            embed.add_field(name="Nickname", value=member.nick if hasattr(member, "nick") else "None", inline=True)
            embed.add_field(name= "UID", value= member.id)
            embed.add_field(name= "SID", value= member.name)
            embed.add_field(name="Account created", value=member.created_at.date(), inline=True)
            embed.add_field(name="Joined this server", value=member.joined_at.date(), inline=True)
            embed.timestamp= datetime.datetime.now(datetime.timezone.utc)

            await logchannel.send(embed = embed)

    @commands.Cog.listener()
    async def on_member_remove(self,member):
        guild = member.guild.id
        chk = await self.check_log_channel(guild)
        if chk == True:
            logchnl, _ = await self.get_log_channel(guild)
            logchannel = self.bot.get_channel(logchnl)
            embed = discord.Embed(color=0xed8796,title="Member Left",description=f"Member {member.mention} has left the server .")

            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar)

            embed.add_field(name="Full name", value=member.global_name, inline=True)
            embed.add_field(name= "UID", value= member.id)
            embed.add_field(name= "SID", value= member.name)
            embed.add_field(name="Account created", value=member.created_at.date(), inline=True)
            embed.add_field(name="Joined this server", value=member.joined_at.date(), inline=True)
            embed.add_field(name="Left this server", value=date.today(), inline=True)
            embed.timestamp= datetime.datetime.now(datetime.timezone.utc)

            await logchannel.send(embed = embed)


async def setup(bot):
    await bot.add_cog(logger(bot))
