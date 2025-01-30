import discord
from discord.ext import commands
import os

class Cogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['nc','newCog','addcog','addCog'])
    @commands.is_owner()
    async def newcog(self, ctx):
        if str(ctx.message.attachments) == '[]':
            await ctx.send(content='No attachements were found', delete_after=5)
            return
        else:
            try:
                await ctx.message.attachments[0].save(fp="Cogs/{}".format(ctx.message.attachments[0].filename))
                await ctx.send(content='Cog has been successfully uploaded', delete_after=5)
                await ctx.message.delete()
            except Exception as exr:
                await ctx.send(content=exr, delete_after=5)

    @commands.command(aliases=['rmc','delcog','rmCog','RmCog','Rmcog'])
    @commands.is_owner()
    async def rmcog(self ,ctx, cog):
        try:
            os.remove('Cogs/'+cog+'.py')
            b = "Cog deleted successfully"
            await ctx.message.delete()
        except Exception:
            b = "Failed to delete cog , check name?"
            await ctx.message.delete()
        await ctx.send(content='```sh\n'+b+'\n```',delete_after=5)
        
    @commands.command(aliases=['dlcog','getcog'])
    @commands.is_owner()
    async def dcog(self, ctx, cog):
        await ctx.message.delete()
        await ctx.send(file=discord.File('Cogs/'+cog+'.py'))

async def setup(bot):
    await bot.add_cog(Cogger(bot))
