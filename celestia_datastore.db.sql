BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Points" (
	"uid"	INTEGER NOT NULL,
	"gid"	INTEGER NOT NULL,
	"points"	INTEGER NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	"display_name"	TEXT NOT NULL,
	PRIMARY KEY("uid","gid")
);
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
COMMIT;
