PRAGMA encoding="UTF-8";
CREATE TABLE IF NOT EXISTS strings (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  language VARCHAR(10) NOT NULL,
  category VARCHAR(255) NOT NULL DEFAULT 'none',
  key VARCHAR(255) NOT NULL,
  value TEXT NOT NULL,
  description TEXT,
  updated INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_lang_cat_key ON strings(language, category, key);

