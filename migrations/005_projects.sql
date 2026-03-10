-- Add projects table and group existing pages by hostname

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    hostname TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE pages
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;

INSERT INTO projects (name, base_url, hostname)
SELECT DISTINCT
    lower((regexp_match(url, '^(?:[a-zA-Z][a-zA-Z0-9+.-]*://)?([^/:?#]+)'))[1]) AS name,
    COALESCE(NULLIF((regexp_match(url, '^([a-zA-Z][a-zA-Z0-9+.-]*)://'))[1], ''), 'https')
        || '://'
        || lower((regexp_match(url, '^(?:[a-zA-Z][a-zA-Z0-9+.-]*://)?([^/:?#]+)'))[1]) AS base_url,
    lower((regexp_match(url, '^(?:[a-zA-Z][a-zA-Z0-9+.-]*://)?([^/:?#]+)'))[1]) AS hostname
FROM pages
WHERE (regexp_match(url, '^(?:[a-zA-Z][a-zA-Z0-9+.-]*://)?([^/:?#]+)'))[1] IS NOT NULL
ON CONFLICT (hostname) DO NOTHING;

UPDATE pages
SET project_id = projects.id
FROM projects
WHERE pages.project_id IS NULL
  AND projects.hostname = lower((regexp_match(pages.url, '^(?:[a-zA-Z][a-zA-Z0-9+.-]*://)?([^/:?#]+)'))[1]);

CREATE INDEX IF NOT EXISTS idx_pages_project_id ON pages (project_id);

DROP TRIGGER IF EXISTS projects_updated_at ON projects;
CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
