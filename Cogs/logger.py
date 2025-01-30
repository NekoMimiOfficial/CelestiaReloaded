import discord
from discord.ext import commands
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
            

    def create_log_channel(self,guild,channel):
        base = 'dataStore/'
        try:
            os.mkdir(base)
        except:
            pass
        guild = str(guild)
        file = open(base+guild+'.txt','w+')
        file.write(str(channel))
        file.close()

    def get_log_channel(self,guild):
        base = 'dataStore/'
        guild = str(guild)
        file = open(base+guild+'.txt','r')
        channel = file.read()
        channel = int(channel)
        return channel

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


    @commands.command()
    @commands.guild_only()
    async def modlogsetup(self,ctx,chnl:discord.TextChannel):
        channel = chnl.id
        guild = ctx.guild.id
        if ctx.author == ctx.guild.owner:
            self.create_log_channel(guild,channel)
            await ctx.send(f"Bound logs to channel `{chnl.name}` !",delete_after=8)
        else:
            await ctx.send(f"Sorry ... only the Guild Owner can run this command")

    @commands.command()
    @commands.guild_only()
    async def removemodlog(self,ctx):
        if ctx.author.id == ctx.guild.owner.id:
            guild = ctx.guild.id
            work = self.rm_log_channel(guild)
            await ctx.send(work,delete_after=8)
        else:
            await ctx.send("Sorry ... only the Guild Owner can run this command")

    @commands.Cog.listener()
    async def on_message_delete(self,message):
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
                logchnl = self.get_log_channel(guild)
                logchannel = self.bot.get_channel(logchnl)
                embed = discord.Embed(color=0xff5500,title="Message Deleted",description=f"A message by `{author.name}` was deleted that contains \n```\n{content}\n```\nin channel `{channel}`")
                embed.set_thumbnail(url=author.avatar.url)
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
                logchnl = self.get_log_channel(guild)
                logchannel = self.bot.get_channel(logchnl)
                embed = discord.Embed(color=0xffff00,title="Message Edited",description=f"A message by `{author.name}` was edited from \n```\n{contentB}\n```\n to ```\n{contentA}\n```\nin channel `{channel}`")
                embed.set_thumbnail(url=author.avatar.url)
                chk = self.checkEdit(contentB,contentA)
                if chk == True:
                    await logchannel.send(embed=embed)
                else:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self,member):
        guild = member.guild.id
        chk = self.check_log_channel(guild)
        if chk == True:
            logchnl = self.get_log_channel(guild)
            logchannel = self.bot.get_channel(logchnl)
            embed = discord.Embed(color=0x00ff11,title="Member Joined",description=f"Member `{member.name}` has joined the server !")
            await logchannel.send(embed = embed)

    @commands.Cog.listener()
    async def on_member_remove(self,member):
        guild = member.guild.id
        chk = self.check_log_channel(guild)
        if chk == True:
            logchnl = self.get_log_channel(guild)
            logchannel = self.bot.get_channel(logchnl)
            embed = discord.Embed(color=0xff0033,title="Member Left",description=f"Member `{member.name}` has left the server .")
            await logchannel.send(embed = embed)


async def setup(bot):
    await bot.add_cog(logger(bot))
