import discord
from discord import app_commands
from discord.ext import commands

class QueryCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
##############################################

    @app_commands.command(name= "avatar", description= "Returns the avatar of a member")
    @app_commands.describe(member= "Pick a user to get their PFP")
    async def __CMD_avatar(self, interaction: discord.Interaction, member:discord.User= None): #type: ignore
        member= member or interaction.user
        embed= discord.Embed(color= 0xee90ac)
        embed.set_image(url= member.avatar.url) #type: ignore
        await interaction.response.send_message(embed= embed)

    @app_commands.command(name= "invite", description= "Invite Celestia to your own guild!")
    async def __CMD_invite(self, interaction: discord.Interaction):
        await interaction.response.send_message("[Celestia Reloaded in your service](https://discord.com/oauth2/authorize?client_id=795085068552896564&permissions=8&integration_type=0&scope=applications.commands+bot)", ephemeral= True)

##############################################
async def setup(bot: commands.Bot) -> None:
 	await bot.add_cog(QueryCog(bot))
