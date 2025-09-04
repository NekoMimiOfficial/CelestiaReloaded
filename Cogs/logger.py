from datetime import date, time
import datetime
import discord
from discord.ext import commands
from discord import app_commands, role
import os.path

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

    def botToggle(self, guild, toggle):
        base= "dataStore/"
        try:
            os.mkdir(base)
        except:
            pass
        if self.check_log_channel(guild):
            if toggle:
                t= "t"
            else:
                t= "f"
            with open(f"{base}{guild}.txt", "w+") as buffer:
                chanID= buffer.read().split("::", 1)[0]
                buffer.write(f"{chanID}::{t};")
            return "Succesfully toggled the bot filter."
        else:
            return "You seem to not have modlogging enabled in this guild."
            

    def create_log_channel(self,guild,channel):
        base = 'dataStore/'
        try:
            os.mkdir(base)
        except:
            pass
        if self.check_log_channel(guild):
            bot= "f"
            with open(base+guild+".txt", "r") as buffer:
                bot= buffer.read().split("::", 1)[1].split(";", 1)[0]
            with open(base+guild+".txt", "w") as buffer:
                if bot == "f":
                    stat= "0"
                else:
                    stat= "1"
                buffer.write(str(channel)+f"::{stat};")
                return
        guild = str(guild)
        file = open(base+guild+'.txt','w+')
        file.write(str(channel)+"::0;")
        file.close()

    def get_log_channel(self,guild):
        base = 'dataStore/'
        guild = str(guild)
        file = open(base+guild+'.txt','r')
        contents= file.read()
        file.close()
        channel = contents
        if not "::" in channel:
            with open(f"{base}{guild}.txt", "w") as buffer:
                buffer.write(f"{channel.strip()}::f;")
            return (int(channel.strip()), False)
        channel = int(channel.split("::", 1)[0])
        botAllow= contents.split("::", 1)[1].split(";", 1)[0]
        if botAllow == "f":
            botAllow= False
        else:
            botAllow= True
        return (channel, botAllow)

    def check_log_channel(self,guild):
        guild = str(guild)
        base = f'dataStore/{guild}.txt'
        isRight = os.path.exists(base)
        if isRight == True:
            return True
        else:
            return False

    def rm_log_channel(self,guild):
        guild = str(guild)
        base = f'dataStore/{guild}.txt'
        isRight = os.path.exists(base)
        if isRight == True:
            os.remove(f'dataStore/{guild}.txt')
            return "Succesfully removed modlog !"
        else:
            return "Erm .. this server isn't enrolled in the modlog database"


    logging= app_commands.Group(name= "logging", description= "Mod log tools")

    @logging.command(name= "setup", description= "setup the modlog")
    @app_commands.describe(chnl= "Channel to bind the logs to")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def modlogsetup(self, interaction: discord.Interaction, chnl:discord.TextChannel):
        channel = chnl.id
        guild = interaction.guild_id
        self.create_log_channel(guild,channel)
        await interaction.response.send_message(f"Bound logs to channel `{chnl.name}` !")

    @logging.command(name= "disable", description= "disable the modlog")
    @commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def removemodlog(self, interaction: discord.Interaction):
        guild = interaction.guild_id
        work = self.rm_log_channel(guild)
        await interaction.response.send_message(work)

    @logging.command(name= "monitor-bots", description= "Sets whether you want to monitor bot messages")
    @app_commands.describe(toggle= "True for enabling bot monitoring, False otherwise")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    async def monbot(self, interaction: discord.Interaction, toggle: bool):
        guild= interaction.guild_id
        resp= self.botToggle(guild, toggle)
        embed= discord.Embed(color= 0xEE90AC, description=resp)
        await interaction.response.send_message(embed= embed, ephemeral= True)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        if not self.check_log_channel(role.guild.id):
            return
        logchnl, _= self.get_log_channel(role.guild.id)
        embed= discord.Embed(color= 0xb7bdf8, title= "Role Created")
        embed.add_field(name= "Role name", value= role.name, inline= True)
        embed.add_field(name= "Role color", value= role.color, inline= True)
        embed.add_field(name= "Created at", value= role.created_at.date(), inline= True)
        embed.add_field(name= "Permissions", value= str(role.permissions.value), inline= False)
        embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
        await self.bot.get_channel(logchnl).send(embed= embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, roleO: discord.Role, roleN: discord.Role):
        if not self.check_log_channel(roleO.guild.id):
            return
        if roleO.name == roleN.name and roleO.color == roleN.color and roleO.permissions == roleN.permissions:
            return
        logchnl, _= self.get_log_channel(roleO.guild.id)
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
        if not self.check_log_channel(role.guild.id):
            return
        logchnl, _= self.get_log_channel(role.guild.id)
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
            chk = self.check_log_channel(guild)
            if message == '':
                emp = False
            else:
                emp = True
            if chk == True and emp == True:
                author = message.author #Defines the message author
                content = message.content #Defines the message content
                channel = message.channel #Defines the message channel
                logchnl, botAllow = self.get_log_channel(guild)
                logchannel = self.bot.get_channel(logchnl)
                if author.bot:
                    if not botAllow:
                        return
                embed = discord.Embed(color=0xf5bde6,title="Message Deleted",description=f"A message by `{author.name}` was deleted")
                embed.add_field(name= "Message Deleted", value= f"```\n{content}\n```")
                embed.set_thumbnail(url=author.avatar.url)
                embed.set_footer(text= f"In channel: {channel.mention} | ")
                embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
                await logchannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self,before,after):
        if not before.author.id == self.bot.user.id: #Checks the ID, if AuthorID = BotID, return. Else, continue.
            guild = before.guild.id
            chk = self.check_log_channel(guild)
            if chk == True:
                author = before.author #Defines the message author
                contentB = before.content #Defines the message content
                contentA = after.content #Defines the message content
                contentB = self.fixEdit(contentB)
                contentA = self.fixEdit(contentA)
                channel = before.channel #Defines the message channel
                logchnl, botAllow = self.get_log_channel(guild)
                logchannel = self.bot.get_channel(logchnl)
                if author.bot:
                    if not botAllow:
                        return
                embed = discord.Embed(color=0xeed49f,title="Message Edited",description=f"A message by {author.mention} was edited")
                embed.add_field(name= "From", value= f"```\n{contentB}\n```", inline= True)
                embed.add_field(name= "After", value= f"```\n{contentA}\n```", inline= True)
                embed.set_footer(text= f"In channel: {channel.mention} | ")
                embed.timestamp= datetime.datetime.now(datetime.timezone.utc)
                embed.set_thumbnail(url=author.avatar.url)
                chk = self.checkEdit(contentB,contentA)
                if chk == True:
                    await logchannel.send(embed=embed)
                else:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self,member: discord.Member):
        guild = member.guild.id
        chk = self.check_log_channel(guild)
        if chk == True:
            logchnl, _ = self.get_log_channel(guild)
            logchannel = self.bot.get_channel(logchnl)
            embed = discord.Embed(color=0xa6da95,title="Member Joined",description=f"Member {member.mention} has joined the server !")

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
        chk = self.check_log_channel(guild)
        if chk == True:
            logchnl, _ = self.get_log_channel(guild)
            logchannel = self.bot.get_channel(logchnl)
            embed = discord.Embed(color=0xed8796,title="Member Left",description=f"Member {member.mention} has left the server .")

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
