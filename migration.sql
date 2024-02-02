CREATE TABLE links (
    id SERIAL PRIMARY KEY,
    short_id VARCHAR(255) NOT NULL,
    original_url TEXT NOT NULL,
    og_title TEXT,
    og_description TEXT,
    og_image TEXT,
    clicks INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (short_id)
);
