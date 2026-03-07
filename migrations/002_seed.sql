-- Seed data: 3 test pages
INSERT INTO pages (url, name, viewport_width, viewport_height, diff_threshold) VALUES
    ('https://example.com', 'Example.com', 1920, 1080, 0.5),
    ('https://httpbin.org/html', 'HTTPBin HTML', 1920, 1080, 1.0),
    ('https://example.org', 'Example.org', 1280, 720, 0.5)
ON CONFLICT DO NOTHING;
