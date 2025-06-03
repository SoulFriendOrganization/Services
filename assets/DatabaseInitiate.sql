-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --sers Section
-- --Users Table
-- CREATE TABLE users (
-- 	id UUID DEFAULT gen_random_uuid(),
-- 	full_name varchar(255) NOT NULL,
-- 	age smallint NOT NULL,
-- 	CONSTRAINT users_key PRIMARY KEY(id)
-- );

-- --- Users Auth
-- CREATE TABLE user_auths (
-- 	user_id UUID REFERENCES users (id),
-- 	username varchar(100) UNIQUE,
-- 	password varchar(255) NOT NULL
-- );

-- -- Mood Section
-- --- Mood Level Table
-- CREATE TABLE mood (
--     id SMALLINT PRIMARY KEY,
--     name TEXT NOT NULL
-- );

-- -- Isi tabel moods dengan data emosi
-- INSERT INTO moods (id, name) VALUES
-- (6, 'Happiness'),
-- (1, 'Sadness'),
-- (2, 'Fear'),
-- (3, 'Disgust'),
-- (4, 'Anger'),
-- (5, 'Surprise');

-- CREATE TABLE daily_moods (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     user_id UUID REFERENCES users(id) ON DELETE CASCADE,
--     date DATE NOT NULL,
--     mood_level smallint REFERENCES mood(id),
--     notes TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE(user_id, date)
-- );

-- -- Quiz Section
-- -- Tabel quizzes
-- CREATE TABLE quizzes (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
-- 		generated_by_user_id UUID REFERENCES users(id),
--     title VARCHAR(255) NOT NULL,
--     description TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );


-- CREATE TYPE question_type AS ENUM ('multiple_choice', 'multiple_answer');


-- -- Tabel questions
-- CREATE TABLE questions (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
--     question_type question_type,
--     question_text TEXT NOT NULL,
--     possible_answers JSONB NOT NULL,
--     correct_answer JSONB NOT NULL
-- );

-- -- Tabel quiz_attempts
-- CREATE TABLE quiz_attempts (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     user_id UUID REFERENCES users(id) ON DELETE CASCADE,
--     quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
--     attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     expired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '20 Minutes',
-- 		is_completed BOOLEAN,
--     score INTEGER,
--     points_earned INTEGER
-- );

-- -- Tabel attempt_answers
-- CREATE TABLE attempt_answers (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
--     question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
--     user_answer JSONB NOT NULL,
--     is_correct BOOLEAN NOT NULL
-- );

-- -- Daily Scores
-- CREATE TABLE daily_scores (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     user_id UUID REFERENCES users(id) ON DELETE CASCADE,
--     date DATE NOT NULL,
--     score INTEGER NOT NULL,
--     UNIQUE(user_id, date)  -- Memastikan hanya satu entri per pengguna per hari
-- );

-- -- user Preferences Section
-- CREATE TABLE user_preferences (
--     user_id UUID REFERENCES users(id) ON DELETE CASCADE,
--     user_preferences JSONB
-- );

-- -- user collections
-- CREATE TABLE user_collections (
-- 	user_id UUID REFERENCES users(id) ON DELETE CASCADE,
-- 	score INT ,
-- 	point_earned INT ,
--  user_condition_summary TEXT,
--  num_quiz_attempt INT
-- )

-- CREATE INDEX idx_daily_moods_user_id ON daily_moods(user_id);
-- CREATE INDEX idx_daily_moods_date ON daily_moods(date);
-- CREATE INDEX idx_daily_moods_user_id_date ON daily_moods(user_id, date);
-- CREATE INDEX idx_quizzes_generated_by_user_id ON quizzes(generated_by_user_id);
-- CREATE INDEX idx_questions_quiz_id ON questions(quiz_id);
-- CREATE INDEX idx_quiz_attempts_user_id ON quiz_attempts(user_id);
-- CREATE INDEX idx_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
-- CREATE INDEX idx_quiz_attempts_user_id_quiz_id ON quiz_attempts(user_id, quiz_id);
-- CREATE INDEX idx_quiz_attempts_attempted_at ON quiz_attempts(attempted_at);
-- CREATE INDEX idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);
-- CREATE INDEX idx_attempt_answers_question_id ON attempt_answers(question_id);
-- CREATE INDEX idx_daily_scores_user_id ON daily_scores(user_id);
-- CREATE INDEX idx_daily_scores_date ON daily_scores(date);
-- CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
-- CREATE INDEX idx_user_collections_user_id ON user_collections(user_id);
