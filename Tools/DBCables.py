import aiosqlite
from typing import Optional, List, Tuple, Any

DB_BUILD_CMD1 = """\
CREATE TABLE IF NOT EXISTS "Guilds" (
	"gid"	INTEGER NOT NULL UNIQUE,
	"identifier"	TEXT,
	"verity_cs"	INTEGER,
	"uc_rolemenu"	TEXT,
	"modlog"	INTEGER,
	"modlog_bot"	INTEGER,
	"welcome_message"	TEXT,
	"join_role"	INTEGER,
	"shop_items"	TEXT,
	"verity_drm"	INTEGER NOT NULL DEFAULT 86400,
	PRIMARY KEY("gid")
);
"""

DB_BUILD_CMD2 = """\
CREATE TABLE IF NOT EXISTS "Users" (
	"uid"	INTEGER NOT NULL UNIQUE,
	"bank"	INTEGER NOT NULL,
	"socialCredit"	INTEGER NOT NULL,
	"discordCredit"	INTEGER NOT NULL,
	"display_name"	TEXT NOT NULL,
	"last_message_ts"	INTEGER NOT NULL,
    "first_added_ts" INTEGER,
	"avg_online"	INTEGER,
	PRIMARY KEY("uid")
);
"""

DB_BUILD_CMD3 = """\
CREATE TABLE IF NOT EXISTS "Points" (
	"uid"	INTEGER NOT NULL,
	"gid"	INTEGER NOT NULL,
	"points"	INTEGER NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	"display_name"	TEXT NOT NULL,
	PRIMARY KEY("uid","gid")
);
"""

class Cables:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        if self.conn is None:
            try:
                self.conn = await aiosqlite.connect(self.db_path)
            except aiosqlite.Error as e:
                print(f"[ fail ] SQLite error during connection: {e}")
                raise

    async def format(self):
        await self.connect()
        async with self.conn.cursor() as cursor:
            await cursor.execute(DB_BUILD_CMD1)
            await cursor.execute(DB_BUILD_CMD2)
            await cursor.execute(DB_BUILD_CMD3)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def _execute(self, cmd: str, values: Optional[Tuple[Any, ...]] = None, commit: bool = True):
        if self.conn is None:
            await self.connect()

        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute(cmd, values or ())
            if commit:
                await self.conn.commit()

        except aiosqlite.OperationalError as e:
            print(f"[ fail ] sqlite operational error: {e}")
        except Exception as e:
            print(f"[ fail ] General error: {e}")
            raise

    async def _fetch_one(self, cmd: str, values: Optional[Tuple[Any, ...]] = None) -> Optional[Tuple[Any, ...]]:
        if self.conn is None:
            await self.connect()

        async with self.conn.cursor() as cursor:
            await cursor.execute(cmd, values or ())
            return await cursor.fetchone()

    async def _fetch_all(self, cmd: str, values: Optional[Tuple[Any, ...]] = None) -> List[Tuple[Any, ...]]:
        if self.conn is None:
            await self.connect()

        async with self.conn.cursor() as cursor:
            await cursor.execute(cmd, values or ())
            return await cursor.fetchall()


    async def init_guild(self, gid: int, gname: str):
        await self._execute(
            "INSERT OR IGNORE INTO Guilds (gid, identifier) VALUES (?, ?)",
            (gid, gname)
        )

    async def denull(self, uid: int, ts):
        await self._execute("UPDATE Users SET first_added_ts = ? WHERE uid = ? AND first_added_ts IS NULL", (ts, uid))

    async def init_user(self, uid: int, gid: int, dname: str, ts: int):
        await self._execute(
            """
            INSERT OR IGNORE INTO Users
            (uid, bank, socialCredit, discordCredit, display_name, last_message_ts, first_added_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (uid, 20, 50, 0, dname, ts, ts),
            commit=False
        )

        await self._execute(
            "INSERT OR IGNORE INTO Points (uid, gid, points, display_name, timestamp) VALUES (?, ?, ?, ?, ?)",
            (uid, gid, 0, dname, ts),
            commit=False
        )
        await self.denull(uid, ts)
        await self.conn.commit()


    async def update_user(self, uid: int, gid: int, dname: str, points: int, bank: int, socialCredit: int, discordCredit: int, ts: int):
        """This function should ONLY be used for the migrator, and that only runs ONCE on an EMPTY db table"""
        await self._execute(
            "INSERT OR IGNORE INTO Points (uid, gid, points, display_name, timestamp) VALUES (?, ?, ?, ?, ?)",
            (uid, gid, points, dname, ts),
            commit=False
        )
        await self._execute(
            "INSERT OR IGNORE INTO Users (uid, bank, socialCredit, discordCredit, display_name, last_message_ts) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, bank, socialCredit, discordCredit, dname, ts)
        )


    async def get_gu_pts(self, uid: int, gid: int) -> int:
        row = await self._fetch_one("SELECT points FROM Points WHERE uid = ? AND gid = ?", (uid, gid))
        return int(row[0]) if row else 0

    async def get_gu_lb(self, gid: int) -> List[Tuple[Any, ...]]:
        return await self._fetch_all("SELECT uid, points, display_name FROM Points where gid = ? ORDER BY points DESC LIMIT 10", (gid,))

    async def get_gu_ts(self, gid: int, uid: int) -> int:
        row = await self._fetch_one("SELECT timestamp FROM Points where gid = ? AND uid = ?", (gid, uid))
        return int(row[0]) if row else 0

    async def inc_gu_points(self, gid: int, uid: int, ts: int, ptr: int, dname: str) -> bool:
        try:
            await self.init_user(uid, gid, dname, ts)

            await self._execute(
                "UPDATE Points SET points = points + ?, timestamp = ?, display_name = ? WHERE uid = ? AND gid = ?",
                (ptr, ts, dname, uid, gid), commit=False
            )
            await self._execute(
                "UPDATE Users SET bank = bank + ?, discordCredit = discordCredit + ?, last_message_ts = ?, display_name = ? WHERE uid = ?",
                (ptr, ptr, ts, dname, uid)
            )
            return True
        except Exception as e:
            print(f"Error in inc_gu_points: {e}")
            return False

    async def inc_u_bank(self, uid: int, ptr: int) -> bool:
        try:
            await self._execute("UPDATE Users SET bank = bank + ? WHERE uid = ?", (ptr, uid))
            return True
        except Exception as e:
            print(f"Error in inc_u_bank: {e}")
            return False

    async def dec_u_bank(self, uid: int, ptr: int) -> bool:
        try:
            await self._execute("UPDATE Users SET bank = bank - ? WHERE uid = ?", (ptr, uid))
            return True
        except Exception as e:
            print(f"Error in dec_u_bank: {e}")
            return False

    async def get_u_bank(self, uid: int) -> int:
        row = await self._fetch_one("SELECT bank FROM Users WHERE uid = ?", (uid,))
        return int(row[0]) if row else 0

    async def get_g_bot(self, gid: int) -> bool:
        row = await self._fetch_one("SELECT modlog_bot FROM Guilds WHERE gid = ?", (gid,))
        return bool(row and row[0])

    async def set_g_bot(self, gid: int, val: int):
        await self._execute("UPDATE Guilds SET modlog_bot = ? WHERE gid = ?", (val, gid))

    async def get_g_mod(self, gid: int) -> int:
        row = await self._fetch_one("SELECT modlog FROM Guilds WHERE gid = ?", (gid,))
        return int(row[0]) if row and row[0] else 0

    async def set_g_mod(self, gid: int, cid: int):
        await self._execute("UPDATE Guilds SET modlog = ? WHERE gid = ?", (cid, gid))

    async def chk_g_mod(self, gid: int) -> bool:
        return await self.get_g_mod(gid) != 0

    async def get_u_last(self, uid: int) -> int:
        row = await self._fetch_one("SELECT last_message_ts FROM Users WHERE uid = ?", (uid,))
        return int(row[0]) if row else 0

    async def get_u_dc(self, uid: int) -> int:
        row = await self._fetch_one("SELECT discordCredit FROM Users WHERE uid = ?", (uid,))
        return int(row[0]) if row else 0

    async def get_u_sc(self, uid: int) -> int:
        row = await self._fetch_one("SELECT socialCredit FROM Users WHERE uid = ?", (uid,))
        return int(row[0]) if row else 0

    async def get_g_uc(self, gid: int) -> str:
        row = await self._fetch_one("SELECT uc_rolemenu FROM Guilds WHERE gid = ?", (gid,))
        return str(row[0]) if row and row[0] else ""

    async def set_g_uc(self, gid: int, jr: str):
        await self._execute("UPDATE Guilds SET uc_rolemenu = ? WHERE gid = ?", (jr, gid))

    async def get_g_jr(self, gid: int) -> int:
        row = await self._fetch_one("SELECT join_role FROM Guilds WHERE gid = ?", (gid,))
        return int(row[0]) if row and row[0] else 0

    async def set_g_jr(self, gid: int, jr: int):
        await self._execute("UPDATE Guilds SET join_role = ? WHERE gid = ?", (jr, gid))

    async def get_g_verity(self, gid: int) -> int:
        row = await self._fetch_one("SELECT verity_cs FROM Guilds WHERE gid = ?", (gid,))
        return int(row[0]) if row and row[0] else 0

    async def set_g_verity(self, gid: int, rid: int):
        await self._execute("UPDATE Guilds SET verity_cs = ? WHERE gid = ?", (rid, gid))

    async def get_g_welcome(self, gid: int) -> str:
        row = await self._fetch_one("SELECT welcome_message FROM Guilds WHERE gid = ?", (gid,))
        return str(row[0]) if row and row[0] else ""

    async def set_g_welcome(self, gid: int, msg: str):
        await self._execute("UPDATE Guilds SET welcome_message = ? WHERE gid = ?", (msg, gid))

    async def get_g_drm(self, gid: int) -> int:
        row = await self._fetch_one("SELECT verity_drm FROM Guilds WHERE gid = ?", (gid,))
        return int(row[0]) if row and row[0] else 86400

    async def set_g_drm(self, gid: int, drm: int):
        await self._execute("UPDATE Guilds SET verity_drm = ? WHERE gid = ?", (drm, gid))

    async def get_u_tg(self, uid: int) -> int:
        row = await self._fetch_one("SELECT avg_online FROM Users WHERE uid = ?", (uid,))
        return int(row[0]) if row and row[0] else 0

    async def set_u_tg(self, uid: int, ts: int):
        await self._execute("UPDATE Users SET avg_online = ? WHERE uid = ?", (ts, uid))

    async def pay(self, uid_s: int, uid_t: int, pts: int, dname_t: str, ts: int):
        await self._execute(
            """
            INSERT OR IGNORE INTO Users
            (uid, bank, socialCredit, discordCredit, display_name, last_message_ts)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (uid_t, 20, 50, 0, dname_t, ts),
            commit=False
        )
        await self._execute("UPDATE Users SET bank = bank - ? WHERE uid = ?", (pts, uid_s), commit=False)
        await self._execute("UPDATE Users SET bank = bank + ? WHERE uid = ?", (pts, uid_t))
