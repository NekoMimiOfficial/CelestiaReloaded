import sqlite3
import time
import multiprocessing

DB_BUILD_CMD1= """\
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

DB_BUILD_CMD2= """\
CREATE TABLE IF NOT EXISTS "Users" (
	"uid"	INTEGER NOT NULL UNIQUE,
	"bank"	INTEGER NOT NULL,
	"socialCredit"	INTEGER NOT NULL,
	"discordCredit"	INTEGER NOT NULL,
	"display_name"	TEXT NOT NULL,
	"last_message_ts"	INTEGER NOT NULL,
	"avg_online"	INTEGER,
	PRIMARY KEY("uid")
);
"""

DB_BUILD_CMD3= """\
CREATE TABLE IF NOT EXISTS "Points" (
	"uid"	INTEGER NOT NULL,
	"gid"	INTEGER NOT NULL,
	"points"	INTEGER NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	"display_name"	TEXT NOT NULL,
	PRIMARY KEY("uid","gid")
);
"""

def t2s(tup: tuple):
    fin_str= "("
    for value in tup:
        fin_str += value + ", "
    fin_str= fin_str[:-2]
    fin_str += ")"
    return fin_str

def quoo(count: int):
    fin= "?, "*count
    fin= fin[:-2]
    return f"({fin})"

class Cables:
    def __init__(self, db: str):
        self.db= db
        self.conn= None
        self.cursor= None

    def format(self):
        self.connect()
        self._cmd(DB_BUILD_CMD1)
        self._cmd(DB_BUILD_CMD2)
        self._cmd(DB_BUILD_CMD3)

    def connect(self):
        try:
            self.conn= sqlite3.connect(self.db)
            self.cursor= self.conn.cursor()
        except sqlite3.Error as e:
            print(f"[ fail ] SQLite error: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

    def _retry(self, cmd: str, values= None):
        i= 0
        while i < 50:
            try:
                self._cmd(cmd, values)
                break
            except:
                i += 1
                time.sleep(5)

        if not i < 50:
            print("[ fail ] sqlite database locked for more than 50 tries, bailing out...")

    def _cmd(self, cmd: str, values= None):
        try:
            if self.cursor and self.conn:
                if values:
                    self.cursor.execute(cmd, values)
                    self.conn.commit()
                else:
                    self.cursor.execute(cmd)
            else:
                raise OSError

        except sqlite3.OperationalError as e:
            if "is locked" in str(e):
                ret_thread= multiprocessing.Process(target= self._retry, args= (cmd, values))
                ret_thread.run()
            else:
                print(f"[ fail ] sqlite error: {e}")

        except Exception as e:
            print(f"[ fail ] General error: {e}")

    def _inserter(self, table: str, fields: tuple, values: tuple):
        self._cmd(f"INSERT OR IGNORE INTO {table} {t2s(fields)} VALUES {quoo(len(values))}", tuple([str(item) for item in values]))

    def _updater(self, table: str, fields: tuple, values: tuple):
        self._cmd(f"INSERT OR REPLACE INTO {table} {t2s(fields)} VALUES {quoo(len(values))}", tuple([str(item) for item in values]))

    def init_guild(self, gid: int, gname: str):
        self._inserter("Guilds", ("gid", "identifier"), (gid, gname))

    def denull(self, uid: int, ts):
        self._cmd(f"UPDATE Users SET first_added_ts = {ts} WHERE uid = {uid} AND first_added_ts IS NULL")

    def init_user(self, uid: int, gid: int, dname: str, ts):
        self._inserter("Users", ("uid", "bank", "socialCredit", "discordCredit", "display_name", "last_message_ts", "first_added_ts"), (uid, 20, 50, 0, dname, ts, ts))
        self._inserter("Points", ("uid", "gid", "points", "display_name", "timestamp"), (uid, gid, 0, dname, ts))
        self.denull(uid, ts)

    def update_user(self, uid: int, gid: int, dname: str, points: int, bank: int, socialCredit: int, discordCredit: int, ts: int):
        "This function should ONLY be used for the migrator, and that only runs ONCE on an EMPTY db table"
        self._inserter("Points", ("uid", "gid", "points", "display_name", "timestamp"), (uid, gid, points, dname, ts))
        self._inserter("Users", ("uid", "bank", "socialCredit", "discordCredit", "display_name", "last_message_ts"), (uid, bank, socialCredit, discordCredit, dname, ts))

    def get_gu_pts(self, uid: int, gid: int):
        if self.cursor:
            self._cmd(f"SELECT points FROM Points WHERE uid = ? AND gid = ?", (str(uid), str(gid)))
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]
        return 0

    def get_gu_lb(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT uid, points, display_name FROM Points where gid = ? ORDER BY points DESC LIMIT 10", (str(gid), ))
            res= self.cursor.fetchall()
            return res
        return []

    def get_gu_ts(self, gid: int, uid: int):
         if self.cursor:
            self._cmd(f"SELECT timestamp FROM Points where gid = ? AND uid = ?", (str(gid), str(uid)))
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]

    def inc_gu_points(self, gid: int, uid: int, ts: int, ptr: int, dname: str):
        if self.cursor:
            try:
                self.init_user(uid, gid, dname, ts)
                self._cmd(f"UPDATE Points SET points = points + ?, timestamp = ?, display_name = ? WHERE uid = ? AND gid = ?", (str(ptr), str(ts), str(dname), str(uid), str(gid)))
                self._cmd(f"UPDATE Users SET bank = bank + ?, discordCredit = discordCredit + ?, last_message_ts = ?, display_name = ? WHERE uid = ?", (str(ptr), str(ptr), str(ts), str(dname), str(uid)))
                return True
            except:
                return False
        return False

    def inc_u_bank(self, uid: int, ptr: int):
        if self.cursor:
            try:
                self._cmd(f"UPDATE Users SET bank = bank + ? WHERE uid = ?", (str(ptr), str(uid)))
                return True
            except:
                return False
        return False

    def dec_u_bank(self, uid: int, ptr: int):
        if self.cursor:
            try:
                self._cmd(f"UPDATE Users SET bank = bank - ? WHERE uid = ?", (str(ptr), str(uid)))
                return True
            except:
                return False
        return False


    def get_u_bank(self, uid: int):
        if self.cursor:
            self._cmd(f"SELECT bank FROM Users WHERE uid = {uid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return int(res[0][0])
        return 0

    def get_g_bot(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT modlog_bot FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return False
            if res[0][0] == 0:
                return False
            else:
                return True

    def set_g_bot(self, gid: int, val: int):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET modlog_bot = {val} WHERE gid = {gid}")

    def get_g_mod(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT modlog FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            if not res[0][0]:
                return 0
            return int(res[0][0])

    def set_g_mod(self, gid: int, cid: int):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET modlog = {cid} WHERE gid = {gid}")

    def chk_g_mod(self, gid: int):
        try:
            res= self.get_g_mod(gid)
            if res:
                if not res == 0:
                    return True
        except:
            return False
        return False

    def get_u_last(self, uid: int):
        if self.cursor:
            self._cmd(f"SELECT last_message_ts FROM Users WHERE uid = {uid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]
        return 0

    def get_u_dc(self, uid: int):
        if self.cursor:
            self._cmd(f"SELECT discordCredit FROM Users WHERE uid = {uid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]

    def get_u_sc(self, uid: int):
        if self.cursor:
            self._cmd(f"SELECT socialCredit FROM Users WHERE uid = {uid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]

    def get_g_uc(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT uc_rolemenu FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]

    def set_g_uc(self, gid: int, jr: int):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET uc_rolemenu = {jr} WHERE gid = {gid}")

    def get_g_jr(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT join_role FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            return res[0][0]

    def set_g_jr(self, gid: int, jr: int):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET join_role = {jr} WHERE gid = {gid}")

    def get_g_verity(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT verity_cs FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            if not res[0][0]:
                return 0
            return int(res[0][0])
        return 0

    def set_g_verity(self, gid: int, rid: int):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET verity_cs = {rid} WHERE gid = {gid}")

    def get_g_welcome(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT welcome_message FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return ""
            if not res[0][0]:
                return ""
            if res[0][0]:
                return res[0][0]
            return ""

    def set_g_welcome(self, gid: int, msg: str):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET welcome_message = \"{msg}\" WHERE gid = {gid}")

    def get_g_drm(self, gid: int):
        if self.cursor:
            self._cmd(f"SELECT verity_drm FROM Guilds WHERE gid = {gid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 86400
            return res[0][0]
        return 86400

    def set_g_drm(self, gid: int, drm: int):
        if self.cursor:
            self._cmd(f"UPDATE Guilds SET verity_drm = {drm} WHERE gid = {gid}")

    def get_u_tg(self, uid: int):
        if self.cursor:
            self._cmd(f"SELECT avg_online FROM Users WHERE uid = {uid}")
            res= self.cursor.fetchall()
            if len(res) < 1:
                return 0
            if not res[0][0]:
                return 0
            return res[0][0]
        return 0

    def set_u_tg(self, uid: int, ts: int):
        if self.cursor:
            self._cmd(f"UPDATE Users SET avg_online = {ts} WHERE uid = {uid}")

    def pay(self, uid_s: int, uid_t: int, pts: int, dname_t: str, ts):
        if self.cursor:
            self._inserter("Users", ("uid", "bank", "socialCredit", "discordCredit", "display_name", "last_message_ts"), (uid_t, 20, 50, 0, dname_t, ts))
            self._cmd(f"UPDATE Users SET bank = bank - {pts} WHERE uid = {uid_s}")
            self._cmd(f"UPDATE Users SET bank = bank + {pts} WHERE uid = {uid_t}")
