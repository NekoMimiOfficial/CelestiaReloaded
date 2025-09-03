import discord
from discord.ext import commands
from discord import app_commands
from NekoMimi import reg
import random
import asyncio

def getScr(uid, gid):
    regName= "Celestia-Guilds-"+gid
    db= reg.Database(regName)
    q= db.query(uid)
    r= 0
    if q == "":
        return r
    return int(q.split(":")[0])

def writeScr(uid, gid, amt):
    regName= "Celestia-Guilds-"+gid
    db= reg.Database(regName)
    q= db.query(str(uid))
    r= int(q.split(":")[0])
    ts= str(q.split(":")[1])
    r= r+amt
    db.store(str(uid), f"{r}:{ts}")

class Blackjack:
    def __init__(self, gid, uid, money):
        self.deck = self.create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.uid= str(uid)
        self.gid= str(gid)
        self.bet= money
        self.bank= getScr(str(uid), str(gid))

    def create_deck(self):
        """Creates and shuffles a standard 52-card deck."""
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck

    def deal_card(self):
        return self.deck.pop()

    def hit(self, hand):
        hand.append(self.deal_card())

    def calculate_hand_value(self, hand):
        value = 0
        num_aces = 0
        for card in hand:
            rank = card['rank']
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                value += 11
                num_aces += 1
            else:
                value += int(rank)

        while value > 21 and num_aces > 0:
            value -= 10
            num_aces -= 1

        return value

    def get_hand_string(self, hand, hide_dealer_card=False):
        cards = []
        if hide_dealer_card:
            cards.append("??")
            for card in hand[1:]:
                cards.append(f"{card['rank']}{card['suit']}")
            return " | ".join(cards)
        else:
            for card in hand:
                cards.append(f"{card['rank']}{card['suit']}")
            return " | ".join(cards)

    def start_game(self):
        if self.bet*2 > self.bank:
            return False
        self.hit(self.player_hand)
        self.hit(self.dealer_hand)
        self.hit(self.player_hand)
        self.hit(self.dealer_hand)
        return True

    def player_bust(self):
        return self.calculate_hand_value(self.player_hand) > 21

    def dealer_bust(self):
        return self.calculate_hand_value(self.dealer_hand) > 21

    def determine_winner(self):
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)

        if self.player_bust():
            writeScr(self.uid, self.gid, self.bet*-2)
            return f"Player Busts! Dealer wins! You lost {self.bet*2} <:CelestialPoints:1412891132559495178>"
        elif self.dealer_bust():
            writeScr(self.uid, self.gid, self.bet*2)
            return f"Dealer Busts! Player wins! You won {self.bet*2} <:CelestialPoints:1412891132559495178>"
        elif player_value > dealer_value:
            writeScr(self.uid, self.gid, self.bet*2)
            return f"Player wins! You won {self.bet*2} <:CelestialPoints:1412891132559495178>"
        elif dealer_value > player_value:
            writeScr(self.uid, self.gid, self.bet*-2)
            return f"Dealer wins! You lost {self.bet*2} <:CelestialPoints:1412891132559495178>"
        else:
            return "It's a tie!"

class BlackjackView(discord.ui.View):
    def __init__(self, game: Blackjack):
        super().__init__(timeout=300)
        self.game = game
        self.message = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def update_message(self, interaction: discord.Interaction, embed: discord.Embed, view_to_use: discord.ui.View = None):
        if view_to_use is None:
            view_to_use= self

        try:
            await interaction.edit_original_response(embed=embed, view=view_to_use)
        except discord.NotFound:
            self.stop()

    def get_game_state_embed(self):
        embed = discord.Embed(
            title="Blackjack",
            description="The game is in progress!",
            color=0xEE90AC
        )

        player_hand_str = self.game.get_hand_string(self.game.player_hand)
        player_value = self.game.calculate_hand_value(self.game.player_hand)

        dealer_hand_str = self.game.get_hand_string(self.game.dealer_hand, hide_dealer_card=not self.game.game_over)
        dealer_value = self.game.calculate_hand_value(self.game.dealer_hand) if self.game.game_over else "??"

        embed.add_field(name="Player's Hand", value=f"{player_hand_str} ({player_value})", inline=False)
        embed.add_field(name="Dealer's Hand", value=f"{dealer_hand_str} ({dealer_value})", inline=False)

        if self.game.game_over:
            embed.description = self.game.determine_winner()

        return embed

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        self.game.hit(self.game.player_hand)

        if self.game.player_bust():
            self.game.game_over = True
            embed = self.get_game_state_embed()

            for item in self.children:
                item.disabled = True
            await self.update_message(interaction, embed)
            self.stop()
        else:
            embed = self.get_game_state_embed()
            await self.update_message(interaction, embed)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        while self.game.calculate_hand_value(self.game.dealer_hand) < 17:
            self.game.hit(self.game.dealer_hand)
            await asyncio.sleep(0.5)

        self.game.game_over = True

        embed = self.get_game_state_embed()

        for item in self.children:
            item.disabled = True
        await self.update_message(interaction, embed)
        self.stop()

class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="blackjack", description="Starts a game of Blackjack.")
    @app_commands.guild_only()
    @app_commands.describe(bet= "The amount to bet on")
    async def blackjack(self, interaction: discord.Interaction, bet: int= 5):
        bet= bet
        if bet < 0:
            bet= bet* -1
        game = Blackjack(interaction.guild_id, interaction.user.id, bet)
        safeToStart= game.start_game()

        if not safeToStart:
            await interaction.response.send_message(f"Please make sure you have at least {bet*2} <:CelestialPoints:1412891132559495178> to bet else you'd go into debt", ephemeral= True)

        view = BlackjackView(game)

        embed = view.get_game_state_embed()

        initial_message = await interaction.response.send_message(embed=embed, view=view)
        view.message = await initial_message.original_response()

async def setup(bot):
    await bot.add_cog(BlackjackCog(bot))
