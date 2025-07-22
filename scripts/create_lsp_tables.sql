-- LSP Score System Database Schema
-- This script adds necessary columns to existing users table and creates user_scores table

-- =============================================
-- 1. Alter existing users table - add new columns
-- =============================================

-- Add level column if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS level VARCHAR(20) DEFAULT 'BRONZE';
COMMENT ON COLUMN users.level IS 'User tier level: BRONZE, SILVER, GOLD, PLATINUM, etc';

-- Add total_points column if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_points INTEGER DEFAULT 0;
COMMENT ON COLUMN users.total_points IS 'Total accumulated points';

-- =============================================
-- 2. Create user_scores table
-- =============================================
CREATE TABLE IF NOT EXISTS user_scores (
    id SERIAL PRIMARY KEY,                   -- Auto-increment primary key
    user_id VARCHAR(255) NOT NULL,           -- User ID
    score_date DATE NOT NULL,                -- Score date
    dimension VARCHAR(50) NOT NULL,          -- Score dimension: sleep, exercise, diet, mental, etc
    difficulty VARCHAR(20) NOT NULL,         -- Difficulty level: easy, medium, hard, super_hard
    score INTEGER NOT NULL,                  -- Score value
    details JSONB,                          -- Score details in JSON format
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- Creation timestamp
    expire_date TIMESTAMP WITH TIME ZONE,    -- Expiration date
    is_expired BOOLEAN DEFAULT FALSE,        -- Expiration flag
    tier_level VARCHAR(20) DEFAULT 'Bronze', -- User tier when score was earned
    sub_category VARCHAR(50),                -- Sub-category (e.g., duration, quality for sleep)
    UNIQUE(user_id, score_date, dimension, difficulty)  -- Unique constraint
);

-- Add comments for user_scores table
COMMENT ON TABLE user_scores IS 'User score records table';
COMMENT ON COLUMN user_scores.id IS 'Record ID';
COMMENT ON COLUMN user_scores.user_id IS 'User ID';
COMMENT ON COLUMN user_scores.score_date IS 'Score date';
COMMENT ON COLUMN user_scores.dimension IS 'Score dimension: sleep, exercise, diet, mental, environment, social, cognition, prevention';
COMMENT ON COLUMN user_scores.difficulty IS 'Difficulty level: easy, medium, hard, super_hard';
COMMENT ON COLUMN user_scores.score IS 'Score value';
COMMENT ON COLUMN user_scores.details IS 'Score calculation details';
COMMENT ON COLUMN user_scores.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN user_scores.expire_date IS 'Score expiration date';
COMMENT ON COLUMN user_scores.is_expired IS 'Whether the score has expired';
COMMENT ON COLUMN user_scores.tier_level IS 'User tier level when score was earned';
COMMENT ON COLUMN user_scores.sub_category IS 'Sub-category (e.g., duration/quality for sleep dimension)';

-- =============================================
-- 3. Create indexes for user_scores table
-- =============================================

CREATE INDEX IF NOT EXISTS idx_user_scores_user_id 
    ON user_scores(user_id);
COMMENT ON INDEX idx_user_scores_user_id IS 'User ID index for user-based queries';

CREATE INDEX IF NOT EXISTS idx_user_scores_date 
    ON user_scores(score_date);
COMMENT ON INDEX idx_user_scores_date IS 'Date index for date-based queries';

CREATE INDEX IF NOT EXISTS idx_user_scores_user_date 
    ON user_scores(user_id, score_date);
COMMENT ON INDEX idx_user_scores_user_date IS 'Composite index for daily user score queries';

CREATE INDEX IF NOT EXISTS idx_user_scores_expire_date 
    ON user_scores(expire_date) 
    WHERE is_expired = FALSE;
COMMENT ON INDEX idx_user_scores_expire_date IS 'Expiration date index for non-expired records';

CREATE INDEX IF NOT EXISTS idx_user_scores_valid 
    ON user_scores(user_id, is_expired, expire_date);
COMMENT ON INDEX idx_user_scores_valid IS 'Index for valid score queries';

-- =============================================
-- 4. Sample queries
-- =============================================

/*
-- Query user's current valid score total
SELECT user_id, SUM(score) as total_valid_score
FROM user_scores
WHERE user_id = 'user_001' 
  AND is_expired = FALSE 
  AND (expire_date IS NULL OR expire_date > NOW())
GROUP BY user_id;

-- Update user's total points based on valid scores
UPDATE users 
SET total_points = (
    SELECT COALESCE(SUM(score), 0)
    FROM user_scores
    WHERE user_scores.user_id = users.user_id
      AND is_expired = FALSE
      AND (expire_date IS NULL OR expire_date > NOW())
)
WHERE user_id = 'user_001';

-- Query monthly score breakdown
SELECT dimension, difficulty, SUM(score) as total_score
FROM user_scores
WHERE user_id = 'user_001'
  AND score_date >= '2025-07-01'
  AND score_date < '2025-08-01'
GROUP BY dimension, difficulty
ORDER BY dimension, difficulty;
*/

-- =============================================
-- Completion notice
-- =============================================
-- LSP tables setup completed!
-- - Added level and total_points columns to users table
-- - Created user_scores table with all necessary fields and indexes
-- - No foreign key constraints added for easier maintenance