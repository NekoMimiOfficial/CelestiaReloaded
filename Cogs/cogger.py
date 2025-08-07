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

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cogName):
        try:
            await self.bot.reload_extension(f'Cogs.{cogName}')
            await ctx.send(f'Cog `{cogName}` reloaded successfully.')
        except commands.ExtensionNotLoaded:
            await ctx.send(f'Cog `{cogName}` is not loaded.')
        except commands.ExtensionNotFound:
            await ctx.send(f'Cog `{cogName}` not found.')
        except Exception as e:
            await ctx.send(f'Error reloading cog `{cogName}`: {e}')

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cogName):
        try:
            await self.bot.load_extension(f"Cogs.{cogName}")
            await ctx.send(f'Cog `{cogName}` loaded successfully.')
        except commands.ExtensionNotFound:
            await ctx.send(f"Cog `{cogName}` not found.")
        except Exception as e:
            await ctx.send(f'Error reloading cog `{cogName}`: {e}')
     
    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cogName):
        try:
            await self.bot.unload_extension(f"Cogs.{cogName}")
            await ctx.send(f'Cog `{cogName}` unloaded successfully.')
        except commands.ExtensionNotFound:
            await ctx.send(f"Cog `{cogName}` not found.")
        except commands.ExtensionNotLoaded:
            await ctx.send(f'Cog `{cogName}` is not loaded.')
        except Exception as e:
            await ctx.send(f'Error reloading cog `{cogName}`: {e}')

    @commands.command()
    @commands.is_owner()
    async def resync(self, ctx):
        await ctx.send("Resyncing...")
        async with ctx.typing():
            sync= await self.bot.tree.sync()
            await ctx.send(f"{len(sync)} commands synced.")


async def setup(bot):
    await bot.add_cog(Cogger(bot))
