-- Kouga challenge ranking tables (Cloudflare D1 / SQLite)
CREATE TABLE IF NOT EXISTS players (
  xid     TEXT PRIMARY KEY,       -- X (Twitter) handle, lower case, without @ (seen by admins only)
  nick    TEXT NOT NULL,          -- the name shown on the board
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tokens (
  id      TEXT PRIMARY KEY,       -- one per run, issued at the start
  xid     TEXT NOT NULL,
  mode    TEXT NOT NULL,          -- the mode the run started in: normal | hard | super
  ip      TEXT NOT NULL,
  created INTEGER NOT NULL,       -- ms since epoch
  used    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS tokens_ip ON tokens (ip, created);

CREATE TABLE IF NOT EXISTS scores (
  id        TEXT PRIMARY KEY,
  token     TEXT NOT NULL UNIQUE,
  xid       TEXT NOT NULL,
  mode      TEXT NOT NULL,
  score     INTEGER NOT NULL,
  elapsed   REAL NOT NULL,        -- game seconds played
  eaten     INTEGER NOT NULL,
  boxes     INTEGER NOT NULL,
  combo     INTEGER NOT NULL,
  lucky     INTEGER NOT NULL,
  patrols   INTEGER NOT NULL,
  rage      INTEGER NOT NULL,
  nightmare INTEGER NOT NULL,
  status    TEXT NOT NULL,        -- ok (shown) | review (held) | rejected (impossible) | deleted
  reason    TEXT NOT NULL DEFAULT '',
  ip        TEXT NOT NULL,
  created   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS scores_board ON scores (status, xid, score DESC);
CREATE INDEX IF NOT EXISTS scores_ip    ON scores (ip, created);
