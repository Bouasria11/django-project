-- ============================================
-- Films Platform - Database Schema DDL
-- Database: PostgreSQL / SQLite Compatible
-- Generated: 2026-05-08
-- ============================================

-- Enable foreign key support (SQLite)
PRAGMA foreign_keys = ON;

-- ============================================
-- Schema Creation (PostgreSQL)
-- ============================================
CREATE SCHEMA IF NOT EXISTS movies;
SET search_path TO movies, public;

-- ============================================
-- TABLE: movies_user (Custom User Model)
-- Extends Django's AbstractUser
-- ============================================
CREATE TABLE movies_user (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) NOT NULL DEFAULT 'SPECTATOR' CHECK (role IN ('SPECTATOR', 'ADMIN')),
    profile_picture VARCHAR(100) NULL,
    bio TEXT NOT NULL DEFAULT '',
    birth_date DATE NULL
);

-- Indexes for User table
CREATE INDEX idx_user_username ON movies_user(username);
CREATE INDEX idx_user_email ON movies_user(email);
CREATE INDEX idx_user_role ON movies_user(role);
CREATE INDEX idx_user_active ON movies_user(is_active);
CREATE INDEX idx_user_date_joined ON movies_user(date_joined DESC);

-- ============================================
-- TABLE: movies_genre
-- Film genre classification
-- ============================================
CREATE TABLE movies_genre (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Genre table
CREATE UNIQUE INDEX idx_genre_name ON movies_genre(name);
CREATE INDEX idx_genre_created ON movies_genre(created_at);

-- ============================================
-- TABLE: movies_film
-- Core film information
-- ============================================
CREATE TABLE movies_film (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    genre_id BIGINT NULL,
    description TEXT NOT NULL CHECK (LENGTH(description) <= 2000),
    release_date DATE NOT NULL,
    director VARCHAR(200) NOT NULL DEFAULT '',
    duration_minutes INTEGER NULL CHECK (duration_minutes > 0),
    poster VARCHAR(100) NULL,
    trailer_url VARCHAR(200) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_film_genre FOREIGN KEY (genre_id)
        REFERENCES movies_genre(id) ON DELETE SET NULL
);

-- Indexes for Film table
CREATE INDEX idx_film_title ON movies_film(title);
CREATE INDEX idx_film_release_date ON movies_film(release_date DESC);
CREATE INDEX idx_film_genre ON movies_film(genre_id);
CREATE INDEX idx_film_created ON movies_film(created_at DESC);
CREATE INDEX idx_film_director ON movies_film(director);

-- Composite indexes for common query patterns
CREATE INDEX idx_film_title_release ON movies_film(title, release_date DESC);
CREATE INDEX idx_film_genre_release ON movies_film(genre_id, release_date DESC);

-- ============================================
-- TABLE: movies_review
-- User ratings and reviews for films
-- ============================================
CREATE TABLE movies_review (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    film_id BIGINT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NOT NULL DEFAULT '' CHECK (LENGTH(comment) <= 2000),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_review_user FOREIGN KEY (user_id)
        REFERENCES movies_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_film FOREIGN KEY (film_id)
        REFERENCES movies_film(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_film UNIQUE (user_id, film_id)
);

-- Indexes for Review table
CREATE INDEX idx_review_film_created ON movies_review(film_id, created_at DESC);
CREATE INDEX idx_review_user ON movies_review(user_id);
CREATE INDEX idx_review_rating ON movies_review(rating);
CREATE INDEX idx_review_user_film ON movies_review(user_id, film_id);
CREATE INDEX idx_review_film_rating ON movies_review(film_id, rating);

-- Composite covering index for review listing queries
CREATE INDEX idx_review_covering ON movies_review(film_id, created_at DESC, rating)
    INCLUDE (comment);  -- PostgreSQL 11+ (for SQLite, use composite without INCLUDE)

-- ============================================
-- TABLE: movies_watchlist
-- User watchlist tracking
-- ============================================
CREATE TABLE movies_watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    film_id BIGINT NOT NULL,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_watchlist_user FOREIGN KEY (user_id)
        REFERENCES movies_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_watchlist_film FOREIGN KEY (film_id)
        REFERENCES movies_film(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_film UNIQUE (user_id, film_id)
);

-- Indexes for Watchlist table
CREATE INDEX idx_watchlist_user ON movies_watchlist(user_id);
CREATE INDEX idx_watchlist_added ON movies_watchlist(added_at DESC);
CREATE INDEX idx_watchlist_user_added ON movies_watchlist(user_id, added_at DESC);

-- ============================================
-- M2M TABLE: movies_user_favorite_genres
-- Many-to-many relationship between users and genres
-- ============================================
CREATE TABLE movies_user_favorite_genres (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    genre_id BIGINT NOT NULL,
    CONSTRAINT fk_fav_user FOREIGN KEY (user_id)
        REFERENCES movies_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_fav_genre FOREIGN KEY (genre_id)
        REFERENCES movies_genre(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_genre UNIQUE (user_id, genre_id)
);

-- Indexes for Favorite Genres M2M
CREATE INDEX idx_fav_user ON movies_user_favorite_genres(user_id);
CREATE INDEX idx_fav_genre ON movies_user_favorite_genres(genre_id);

-- ============================================
-- TRIGGERS & FUNCTIONS (PostgreSQL only)
-- Auto-update updated_at on row updates
-- ============================================
-- Uncomment for PostgreSQL:
/*
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_film_updated_at
    BEFORE UPDATE ON movies_film
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_review_updated_at
    BEFORE UPDATE ON movies_review
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
*/

-- ============================================
-- VIEWS (Optional - for common aggregations)
-- ============================================

-- View: Film statistics (pre-computed aggregates)
CREATE OR REPLACE VIEW vw_film_stats AS
SELECT
    f.id,
    f.title,
    f.release_date,
    g.name as genre_name,
    COUNT(DISTINCT r.id) as review_count,
    ROUND(AVG(r.rating), 1) as average_rating,
    MAX(r.created_at) as last_review_date
FROM movies_film f
LEFT JOIN movies_genre g ON f.genre_id = g.id
LEFT JOIN movies_review r ON f.id = r.film_id
GROUP BY f.id, f.title, f.release_date, g.name;

-- Index on the view materialization (PostgreSQL)
-- CREATE INDEX idx_vw_film_stats_rating ON vw_film_stats(average_rating DESC);


-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Insert sample genres
-- INSERT INTO movies_genre (name, description) VALUES
-- ('Action', 'Films with high-energy sequences and physical feats'),
-- ('Comedy', 'Films intended to make the audience laugh'),
-- ('Drama', 'Serious, plot-driven films with realistic characters'),
-- ('Science Fiction', 'Films exploring futuristic concepts and technology');

-- Insert sample admin user (password: admin123 - requires proper hashing)
-- INSERT INTO movies_user (
--     username, email, password, role, is_staff, is_superuser, is_active
-- ) VALUES (
--     'admin', 'admin@example.com',
--     'pbkdf2_sha256$260000$...',  -- Use Django's make_password
--     'ADMIN', TRUE, TRUE, TRUE
-- );

-- ============================================
-- PERFORMANCE TUNING (PostgreSQL specific)
-- ============================================

-- Increase shared_buffers for better caching
-- SET shared_buffers = '256MB';

-- Enable connection pooling via pgbouncer recommended for production
-- Configure in separate pgbouncer.ini file

-- Optimize work_mem for complex sorts/joins
-- SET work_mem = '16MB';

-- Enable query plan caching
-- ALTER DATABASE films_platform SET statement_timeout = '30s';
-- ALTER DATABASE films_platform SET lock_timeout = '2s';

-- ============================================
-- BACKUP & MAINTENANCE
-- ============================================

-- Create a function to truncate all tables (testing only)
-- DROP FUNCTION IF EXISTS truncate_all_tables();
-- CREATE FUNCTION truncate_all_tables() RETURNS void AS $$
-- DECLARE
--     row RECORD;
-- BEGIN
--     FOR row IN
--         SELECT tablename FROM pg_tables
--         WHERE schemaname = 'movies'
--     LOOP
--         EXECUTE 'TRUNCATE movies.' || row.tablename || ' RESTART IDENTITY CASCADE';
--     END LOOP;
-- END;
-- $$ LANGUAGE plpgsql;

-- Daily refresh materialized view (if using)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_film_stats;

-- ============================================
-- END OF SCHEMA
-- ============================================
