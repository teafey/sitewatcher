-- Add viewports JSONB array to pages
ALTER TABLE pages ADD COLUMN IF NOT EXISTS viewports JSONB
  DEFAULT '[{"width":1920,"height":1080}]'::jsonb;

-- Backfill existing pages
UPDATE pages SET viewports = jsonb_build_array(
  jsonb_build_object('width', viewport_width, 'height', viewport_height)
) WHERE viewports IS NULL;

-- Add viewport columns to snapshots
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS viewport_width INT;
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS viewport_height INT;

-- Backfill existing snapshots from their page
UPDATE snapshots s SET viewport_width = p.viewport_width, viewport_height = p.viewport_height
FROM pages p WHERE s.page_id = p.id AND s.viewport_width IS NULL;

-- Index for per-viewport queries
CREATE INDEX IF NOT EXISTS idx_snapshots_page_viewport
  ON snapshots (page_id, viewport_width, viewport_height, captured_at DESC);
