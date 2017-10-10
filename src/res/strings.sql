CREATE TABLE IF NOT EXISTS strings (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  language VARCHAR(10) NOT NULL,
  key VARCHAR(255) NOT NULL,
  value TEXT NOT NULL,
  description TEXT,
  updated INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_language_key ON strings(language, key);
