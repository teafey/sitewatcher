-- SiteWatcher: Initial schema
-- Run this in Supabase SQL Editor

-- Pages table
CREATE TABLE IF NOT EXISTS pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    name TEXT,
    viewport_width INT DEFAULT 1920,
    viewport_height INT DEFAULT 1080,
    check_interval_hours INT DEFAULT 24,
    diff_threshold FLOAT DEFAULT 0.5,
    ignore_selectors TEXT[] DEFAULT '{}',
    wait_for_selector TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Snapshots table
CREATE TABLE IF NOT EXISTS snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    screenshot_path TEXT,
    dom_text TEXT,
    dom_hash TEXT,
    diff_percent FLOAT,
    diff_image_path TEXT,
    text_diff TEXT,
    has_changes BOOLEAN DEFAULT false,
    error_message TEXT,
    captured_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_snapshots_page_captured
    ON snapshots (page_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_pages_active
    ON pages (is_active);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pages_updated_at
    BEFORE UPDATE ON pages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
