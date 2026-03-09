-- Add capture options to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS scroll_to_bottom BOOLEAN DEFAULT true;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS max_scrolls INT DEFAULT 10 CHECK (max_scrolls >= 1 AND max_scrolls <= 100);
ALTER TABLE pages ADD COLUMN IF NOT EXISTS wait_seconds INT DEFAULT 3 CHECK (wait_seconds >= 1 AND wait_seconds <= 30);
