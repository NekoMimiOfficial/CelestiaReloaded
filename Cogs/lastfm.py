import discord
from discord.ext import commands
from discord import app_commands

import pylast
import aiosqlite
import aiohttp
import hashlib
import os

from NekoMimi import reg

DB_PATH = "celestia_lfm.db"
LASTFM_API_KEY = reg.readCell("lfm_key")
LASTFM_API_SECRET = reg.readCell("lfm_sec")
LASTFM_API_ROOT = "https://ws.audioscrobbler.com/2.0/"

PERIOD_MAP = {
    "overall": pylast.PERIOD_OVERALL,
    "7day": pylast.PERIOD_7DAYS,
    "1month": pylast.PERIOD_1MONTH,
    "3month": pylast.PERIOD_3MONTHS,
    "6month": pylast.PERIOD_6MONTHS,
    "12month": pylast.PERIOD_12MONTHS,
}

PERIOD_CHOICES = [
    app_commands.Choice(name="overall", value="overall"),
    app_commands.Choice(name="7 days", value="7day"),
    app_commands.Choice(name="1 month", value="1month"),
    app_commands.Choice(name="3 months", value="3month"),
    app_commands.Choice(name="6 months", value="6month"),
    app_commands.Choice(name="1 year", value="12month"),
]


def sign_paw_print(params: dict) -> str:
    sorted_pairs = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    return hashlib.md5((sorted_pairs + LASTFM_API_SECRET).encode()).hexdigest()


async def fetch_kitty_token() -> str:
    params = {
        "method": "auth.getToken",
        "api_key": LASTFM_API_KEY,
    }
    params["api_sig"] = sign_paw_print(params)
    params["format"] = "json"
    async with aiohttp.ClientSession() as session:
        async with session.get(LASTFM_API_ROOT, params=params) as resp:
            data = await resp.json()
            if "error" in data:
                raise ValueError(data.get("message", "couldn't get token from last.fm 😿"))
            return data["token"]


async def trade_token_for_sesh(token: str) -> tuple[str, str]:
    params = {
        "method": "auth.getSession",
        "api_key": LASTFM_API_KEY,
        "token": token,
    }
    params["api_sig"] = sign_paw_print(params)
    params["format"] = "json"
    async with aiohttp.ClientSession() as session:
        async with session.get(LASTFM_API_ROOT, params=params) as resp:
            data = await resp.json()
            if "error" in data:
                raise ValueError(data.get("message", "last.fm said no 😿"))
            sesh = data["session"]
            return sesh["name"], sesh["key"]


def build_purrfect_network(session_key: str) -> pylast.LastFMNetwork:
    return pylast.LastFMNetwork(
        api_key=LASTFM_API_KEY,
        api_secret=LASTFM_API_SECRET,
        session_key=session_key,
    )


async def fetch_kitty_data(discord_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT lastfm_username, session_key FROM kitty_lastfm WHERE discord_id = ?",
            (discord_id,),
        ) as cursor:
            return await cursor.fetchone()


async def save_kitty_sesh(discord_id: int, username: str, session_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO kitty_lastfm (discord_id, lastfm_username, session_key)
            VALUES (?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET
                lastfm_username = excluded.lastfm_username,
                session_key     = excluded.session_key
            """,
            (discord_id, username, session_key),
        )
        await db.commit()


class ConfirmAuthView(discord.ui.View):
    def __init__(self, token: str, discord_id: int):
        super().__init__(timeout=300)
        self.token = token
        self.discord_id = discord_id
        auth_url = f"https://www.last.fm/api/auth/?api_key={LASTFM_API_KEY}&token={token}"
        self.add_item(
            discord.ui.Button(
                label="authorize on last.fm~ 🎵",
                url=auth_url,
                style=discord.ButtonStyle.link,
            )
        )

    @discord.ui.button(label="i've authorized it! ✅", style=discord.ButtonStyle.green)
    async def nyaa_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "nya~ this isn't ur auth flow! 😾", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            username, sesh_key = await trade_token_for_sesh(self.token)
            await save_kitty_sesh(self.discord_id, username, sesh_key)
            self.stop()
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(
                content=f"nyaa~ linked **{username}** successfully! 🐾",
                view=self,
            )
        except ValueError as e:
            await interaction.followup.send(
                f"mrrrow... last.fm said: `{e}`\nmake sure u actually clicked authorize on the last.fm page nya~ 😿",
                ephemeral=True,
            )

    @discord.ui.button(label="cancel ✗", style=discord.ButtonStyle.red)
    async def uwu_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "nya~ this isn't ur auth flow! 😾", ephemeral=True
            )
            return
        self.stop()
        await interaction.response.edit_message(
            content="cancelled~ come back whenever nya 🐱", view=None
        )

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class LastFMGroup(app_commands.Group, name="lastfm", description="last.fm integration nya~ 🎵"):

    @app_commands.command(name="login", description="nyaa~ link ur last.fm account!")
    async def paw_at_login(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        token = await fetch_kitty_token()
        view = ConfirmAuthView(token=token, discord_id=interaction.user.id)
        await interaction.followup.send(
            "click below to authorize on last.fm, then hit **i've authorized it!** when done~ 🐾",
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name="logout", description="unlink ur last.fm account :(")
    async def wave_goodbye(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM kitty_lastfm WHERE discord_id = ?", (interaction.user.id,)
            )
            await db.commit()
        await interaction.response.send_message(
            "mew... unlinked ur account~ come back soon! 🐱", ephemeral=True
        )

    @app_commands.command(name="np", description="what r u listening to rn? 🎶")
    @app_commands.describe(member="whose np? (defaults to u~)")
    async def purr_now_playing(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        target = member or interaction.user
        row = await fetch_kitty_data(target.id)
        if not row:
            msg = (
                "u haven't linked last.fm yet nya~ use `/lastfm login`!"
                if target == interaction.user
                else f"{target.mention} hasn't linked last.fm yet nya~"
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        await interaction.response.defer()
        network = build_purrfect_network(row["session_key"])
        lfm_user = network.get_user(row["lastfm_username"])
        track = lfm_user.get_now_playing()

        if not track:
            await interaction.followup.send(
                f"**{row['lastfm_username']}** isn't playing anything rn... 😴"
            )
            return

        artist = track.get_artist().get_name()
        title = track.get_title()
        album_obj = track.get_album()
        album = album_obj.get_name() if album_obj else None
        cover = track.get_cover_image() or discord.Embed.Empty

        embed = discord.Embed(
            title=f"🎵 {title}",
            description=f"by **{artist}**" + (f"\n*{album}*" if album else ""),
            color=0xD51007,
        )
        embed.set_thumbnail(url=cover)
        embed.set_author(
            name=f"{row['lastfm_username']} is listening~",
            icon_url=target.display_avatar.url,
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="recent", description="ur recent scrobbles nya~")
    @app_commands.describe(member="whose scrobbles? (defaults to u~)", limit="how many? (max 10)")
    async def sniff_recent_tracks(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
        limit: app_commands.Range[int, 1, 10] = 5,
    ):
        target = member or interaction.user
        row = await fetch_kitty_data(target.id)
        if not row:
            await interaction.response.send_message(
                "that user hasn't linked last.fm nya~", ephemeral=True
            )
            return

        await interaction.response.defer()
        network = build_purrfect_network(row["session_key"])
        lfm_user = network.get_user(row["lastfm_username"])
        recent = lfm_user.get_recent_tracks(limit=limit)

        if not recent:
            await interaction.followup.send("no scrobbles found nya~ 😿")
            return

        lines = [
            f"`{i}.` **{pt.track.get_title()}** — {pt.track.get_artist().get_name()}"
            for i, pt in enumerate(recent, 1)
        ]

        embed = discord.Embed(
            title=f"🎵 recent scrobbles for {row['lastfm_username']}~",
            description="\n".join(lines),
            color=0xD51007,
        )
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="topartists", description="ur top artists nya~ 🐾")
    @app_commands.describe(
        member="whose top artists? (defaults to u~)",
        period="time period~",
        limit="how many? (max 10)",
    )
    @app_commands.choices(period=PERIOD_CHOICES)
    async def beg_for_top_artists(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
        period: str = "overall",
        limit: app_commands.Range[int, 1, 10] = 5,
    ):
        target = member or interaction.user
        row = await fetch_kitty_data(target.id)
        if not row:
            await interaction.response.send_message(
                "that user hasn't linked last.fm nya~", ephemeral=True
            )
            return

        await interaction.response.defer()
        network = build_purrfect_network(row["session_key"])
        lfm_user = network.get_user(row["lastfm_username"])
        top_artists = lfm_user.get_top_artists(period=PERIOD_MAP[period], limit=limit)

        lines = [
            f"`{i}.` **{ta.item.get_name()}** — {int(ta.weight):,} plays"
            for i, ta in enumerate(top_artists, 1)
        ]

        embed = discord.Embed(
            title=f"🎤 top artists for {row['lastfm_username']} ({period})~",
            description="\n".join(lines),
            color=0xD51007,
        )
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="toptracks", description="ur top tracks nya~ 🎵")
    @app_commands.describe(
        member="whose top tracks? (defaults to u~)",
        period="time period~",
        limit="how many? (max 10)",
    )
    @app_commands.choices(period=PERIOD_CHOICES)
    async def nuzzle_top_tracks(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
        period: str = "overall",
        limit: app_commands.Range[int, 1, 10] = 5,
    ):
        target = member or interaction.user
        row = await fetch_kitty_data(target.id)
        if not row:
            await interaction.response.send_message(
                "that user hasn't linked last.fm nya~", ephemeral=True
            )
            return

        await interaction.response.defer()
        network = build_purrfect_network(row["session_key"])
        lfm_user = network.get_user(row["lastfm_username"])
        top_tracks = lfm_user.get_top_tracks(period=PERIOD_MAP[period], limit=limit)

        lines = [
            f"`{i}.` **{tt.item.get_title()}** — {tt.item.get_artist().get_name()} ({int(tt.weight):,} plays)"
            for i, tt in enumerate(top_tracks, 1)
        ]

        embed = discord.Embed(
            title=f"🎵 top tracks for {row['lastfm_username']} ({period})~",
            description="\n".join(lines),
            color=0xD51007,
        )
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="profile", description="ur last.fm profile stats nya~ 🐾")
    @app_commands.describe(member="whose profile? (defaults to u~)")
    async def peek_at_profile(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        target = member or interaction.user
        row = await fetch_kitty_data(target.id)
        if not row:
            await interaction.response.send_message(
                "that user hasn't linked last.fm nya~", ephemeral=True
            )
            return

        await interaction.response.defer()
        network = build_purrfect_network(row["session_key"])
        lfm_user = network.get_user(row["lastfm_username"])

        playcount = lfm_user.get_playcount()
        registered = lfm_user.get_registered()
        url = lfm_user.get_url()

        embed = discord.Embed(
            title=f"🎧 {row['lastfm_username']}'s last.fm~",
            url=url,
            color=0xD51007,
        )
        embed.add_field(name="scrobbles nya~", value=f"{int(playcount):,}", inline=True)
        embed.add_field(name="member since~", value=f"<t:{int(registered)}:D>", inline=True)
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)


class LastFMCog(commands.Cog, name="Last.FM nya~"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.kitty_lastfm_group = LastFMGroup()
        bot.tree.add_command(self.kitty_lastfm_group)

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS kitty_lastfm (
                    discord_id      INTEGER PRIMARY KEY,
                    lastfm_username TEXT NOT NULL,
                    session_key     TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def cog_unload(self):
        self.bot.tree.remove_command(self.kitty_lastfm_group.name)


async def setup(bot: commands.Bot):
    await bot.add_cog(LastFMCog(bot))
