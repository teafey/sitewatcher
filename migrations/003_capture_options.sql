-- Add capture options to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS scroll_to_bottom BOOLEAN DEFAULT true;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS max_scrolls INT DEFAULT 10;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS wait_seconds INT DEFAULT 3;
