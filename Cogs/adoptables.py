import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_DB_ADMINS= []

class AdoptCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot= bot
        ALLOWED_DB_ADMINS.append(bot.owner_id)
##############################################

    adopt_commands= app_commands.Group(name= "adoptables", description= "Your adoptable characters, as cute as they can be")

    @adopt_commands.command(name= "add-to-db", description= "Adds a character to the database")
    @app_commands.describe(name= "Character name")
    @app_commands.describe(img_url= "Static url to the image")
    @app_commands.describe(price= "Value of the character")
    async def __CMD_add2db(self, interaction: discord.Interaction, name: str, img_url: str, price: int):
        if not interaction.user.id in ALLOWED_DB_ADMINS:
            await interaction.response.send_message("You are not eligible to perform this action.", ephemeral= True)
            return
        body= f"Score: 0\nValue: **{price}** <:CelestialPoints:1412891132559495178>"
        embed= discord.Embed(color= 0xEE90AC, title= name, description= body)
        embed.set_image(url= img_url)
        await interaction.response.send_message(embed= embed)

##############################################
async def setup(bot: commands.Bot) -> None:
 	await bot.add_cog(AdoptCog(bot))
