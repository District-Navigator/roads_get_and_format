PRAGMA foreign_keys = ON;

-- ======================================================
-- Users
-- ======================================================
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  name TEXT,
  status TEXT DEFAULT 'active',               -- e.g. active, invited, suspended
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT,                             -- soft-delete timestamp or NULL
  last_login_at TEXT,
  UNIQUE(email)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE TRIGGER IF NOT EXISTS trg_update_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
WHEN NEW.updated_at <= OLD.updated_at
BEGIN
  UPDATE users SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- ======================================================
-- Pending Auth Requests
-- (new schema: includes request_type & user_name; email has no FK)
-- ======================================================
CREATE TABLE IF NOT EXISTS pending_auth_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,                         -- no FK constraint (registration can precede users)
  request_type TEXT NOT NULL DEFAULT 'signin', -- 'signin' | 'register'
  user_name TEXT,                              -- optional display name supplied at registration
  token TEXT NOT NULL,                         -- one-time token or code
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'expired')),
  metadata TEXT,                               -- JSON as TEXT for extra info (optional)
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT                               -- optional expiry timestamp (ISO8601 TEXT)
);

CREATE INDEX IF NOT EXISTS idx_pending_auth_requests_email ON pending_auth_requests(email);
CREATE INDEX IF NOT EXISTS idx_pending_auth_requests_token ON pending_auth_requests(token);
CREATE INDEX IF NOT EXISTS idx_pending_auth_requests_status ON pending_auth_requests(status);
CREATE INDEX IF NOT EXISTS idx_pending_auth_requests_expires_at ON pending_auth_requests(expires_at);

-- ======================================================
-- Districts
-- ======================================================
CREATE TABLE IF NOT EXISTS districts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,             -- internal PK
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',            -- e.g. active, archived, disabled
  road_count INTEGER NOT NULL DEFAULT 0,            -- denormalized counter (maintain from app/triggers)
  created_at TEXT NOT NULL DEFAULT (datetime('now')), -- ISO8601 UTC
  created_by INTEGER,                               -- FK -> users(id)
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT,                                  -- soft-delete timestamp or NULL
  district_border_coordinates TEXT,                 -- GeoJSON Polygon as TEXT (or JSON array of rings)
  owner INTEGER,                                    -- owner user id (FK -> users.id)
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (owner) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_districts_status ON districts(status);
CREATE INDEX IF NOT EXISTS idx_districts_owner ON districts(owner);
CREATE INDEX IF NOT EXISTS idx_districts_created_by ON districts(created_by);

CREATE TRIGGER IF NOT EXISTS trg_update_districts_updated_at
AFTER UPDATE ON districts
FOR EACH ROW
WHEN NEW.updated_at <= OLD.updated_at
BEGIN
  UPDATE districts SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- ======================================================
-- Areas
-- ======================================================
CREATE TABLE IF NOT EXISTS areas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  district_id INTEGER NOT NULL,                   -- FK -> districts.id
  name TEXT NOT NULL,
  status TEXT DEFAULT 'active',                   -- e.g. active, archived, disabled
  area_border_coordinates TEXT,                   -- GeoJSON Polygon / MultiPolygon as TEXT
  sub_area INTEGER NOT NULL DEFAULT 0,            -- 0/1 boolean flag, default false
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_by INTEGER,                             -- FK -> users.id (nullable)
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT,                                -- soft-delete timestamp or NULL
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_areas_district ON areas(district_id);
CREATE INDEX IF NOT EXISTS idx_areas_name ON areas(name);
CREATE INDEX IF NOT EXISTS idx_areas_status ON areas(status);

CREATE TRIGGER IF NOT EXISTS trg_update_areas_updated_at
AFTER UPDATE ON areas
FOR EACH ROW
WHEN NEW.updated_at <= OLD.updated_at
BEGIN
  UPDATE areas SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- ======================================================
-- Roads
-- ======================================================
CREATE TABLE IF NOT EXISTS roads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,        -- internal PK
  key TEXT NOT NULL UNIQUE,                    -- stable external identifier / slug
  district_id INTEGER NOT NULL,                -- FK -> districts.id
  name TEXT NOT NULL,
  type TEXT,                                   -- e.g. primary, secondary, residential
  length REAL,                                 -- length in meters
  size TEXT,                                   -- 'small','medium','large' (enum-like TEXT; enforce in app or via CHECK)
  segments TEXT,                               -- JSON array of segment objects (as TEXT)
  areas TEXT,                                  -- JSON array of area ids this road intersects/belongs to (as TEXT)
  coordinates TEXT,                            -- GeoJSON LineString or JSON array of [lng,lat] pairs (as TEXT)
  sub_area_ids TEXT,                           -- JSON array of sub-area ids (new canonical field)
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_updated TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT,                             -- soft-delete timestamp or NULL
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_roads_district ON roads(district_id);
CREATE INDEX IF NOT EXISTS idx_roads_name ON roads(name);
CREATE INDEX IF NOT EXISTS idx_roads_type ON roads(type);

-- Optional FTS5 virtual table for text search (only if your D1 instance supports FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS roads_fts USING fts5(
  name, segments, coordinates, content='roads', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS trg_roads_ai AFTER INSERT ON roads BEGIN
  INSERT INTO roads_fts(rowid, name, segments, coordinates) VALUES (new.id, new.name, new.segments, new.coordinates);
END;
CREATE TRIGGER IF NOT EXISTS trg_roads_ad AFTER DELETE ON roads BEGIN
  INSERT INTO roads_fts(roads_fts, rowid, name, segments, coordinates) VALUES('delete', old.id, old.name, old.segments, old.coordinates);
END;
CREATE TRIGGER IF NOT EXISTS trg_roads_au AFTER UPDATE ON roads BEGIN
  INSERT INTO roads_fts(roads_fts, rowid, name, segments, coordinates) VALUES('delete', old.id, old.name, old.segments, old.coordinates);
  INSERT INTO roads_fts(rowid, name, segments, coordinates) VALUES (new.id, new.name, new.segments, new.coordinates);
END;

CREATE TRIGGER IF NOT EXISTS trg_update_roads_last_updated
AFTER UPDATE ON roads
FOR EACH ROW
WHEN NEW.last_updated <= OLD.last_updated
BEGIN
  UPDATE roads SET last_updated = datetime('now') WHERE id = OLD.id;
END;

-- ======================================================
-- District Members
-- ======================================================
CREATE TABLE IF NOT EXISTS district_members (
  district_id INTEGER NOT NULL,     -- FK -> districts.id
  user_id INTEGER NOT NULL,         -- FK -> users.id
  role TEXT NOT NULL DEFAULT 'member', -- e.g. member, admin, editor, viewer
  permissions TEXT,                 -- optional JSON array or object of fine-grained permissions (store as TEXT)
  joined_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT,                  -- soft-remove membership without dropping row
  active INTEGER NOT NULL DEFAULT 1, -- 0/1 flag; renamed from is_active to active
  PRIMARY KEY (district_id, user_id),
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_district_members_user ON district_members(user_id);
CREATE INDEX IF NOT EXISTS idx_district_members_role ON district_members(role);
CREATE INDEX IF NOT EXISTS idx_district_members_active ON district_members(active);

CREATE TRIGGER IF NOT EXISTS trg_update_district_members_updated_at
AFTER UPDATE ON district_members
FOR EACH ROW
WHEN NEW.updated_at <= OLD.updated_at
BEGIN
  UPDATE district_members SET updated_at = datetime('now') WHERE district_id = OLD.district_id AND user_id = OLD.user_id;
END;

-- ======================================================
-- User Road Data
-- ======================================================
CREATE TABLE IF NOT EXISTS user_road_data (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  road_id INTEGER NOT NULL,           -- FK -> roads.id
  user_id INTEGER NOT NULL,           -- FK -> users.id
  district_id INTEGER NOT NULL,       -- denormalized for fast scoping (FK -> districts.id)

  -- Denormalized fields copied from roads
  areas TEXT,                         -- JSON array of area ids or objects (as TEXT)
  size TEXT,                          -- 'small'|'medium'|'large' (enum-like TEXT)

  -- Measurement fields
  distance_ft REAL,                   -- distance in feet (use REAL for fractional feet)
  time_seconds INTEGER CHECK(time_seconds BETWEEN 0 AND 30), -- time in seconds, 0..30

  created_at TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY (road_id) REFERENCES roads(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_urd_road ON user_road_data(road_id);
CREATE INDEX IF NOT EXISTS idx_urd_user ON user_road_data(user_id);
CREATE INDEX IF NOT EXISTS idx_urd_district ON user_road_data(district_id);
CREATE INDEX IF NOT EXISTS idx_urd_size ON user_road_data(size);
CREATE INDEX IF NOT EXISTS idx_urd_distance ON user_road_data(distance_ft);
CREATE INDEX IF NOT EXISTS idx_urd_time ON user_road_data(time_seconds);

CREATE INDEX IF NOT EXISTS idx_urd_road_district_created ON user_road_data(road_id, district_id, created_at DESC);

-- Optional: trigger to validate that user_road_data.district_id matches roads.district_id
-- (uncomment to enable DB-side enforcement; note this adds write overhead)
-- CREATE TRIGGER IF NOT EXISTS trg_validate_urd_district
-- BEFORE INSERT ON user_road_data
-- FOR EACH ROW
-- BEGIN
--   SELECT CASE
--     WHEN (SELECT district_id FROM roads WHERE id = NEW.road_id) IS NULL THEN
--       RAISE(ABORT, 'Invalid road_id')
--     WHEN (SELECT district_id FROM roads WHERE id = NEW.road_id) != NEW.district_id THEN
--       RAISE(ABORT, 'district_id does not match road.district_id')
--   END;
-- END;

-- ======================================================
-- Events (optional audit / activity log)
-- ======================================================
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  district_id INTEGER,
  actor_id INTEGER,
  object_type TEXT,                    -- 'road','area','user_road_data','district', etc.
  object_id INTEGER,
  event_type TEXT NOT NULL,            -- 'create','update','delete','comment', etc.
  payload TEXT,                        -- JSON payload with details
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
  FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_district ON events(district_id);
CREATE INDEX IF NOT EXISTS idx_events_actor ON events(actor_id);

-- ======================================================
-- Attachments (optional - recommended for photos / avatars)
-- ======================================================
CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  organization_id INTEGER,               -- optional if you later introduce orgs/tenants
  owner_id INTEGER,                      -- FK -> users(id)
  filename TEXT NOT NULL,
  content_type TEXT,
  storage_key TEXT NOT NULL,             -- R2/S3 key or URL
  size INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_attachments_owner ON attachments(owner_id);

-- ======================================================
-- End of schema
-- ======================================================
