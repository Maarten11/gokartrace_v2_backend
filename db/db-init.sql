CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    teamname VARCHAR(50) UNIQUE,
    laps INT DEFAULT 0,
    lastlap TIMESTAMP DEFAULT now(),
    laptime INT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password BYTEA
);

CREATE TYPE race_status AS ENUM('Started', 'Paused', 'Stopped');

CREATE TABLE IF NOT EXISTS races (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    status race_status DEFAULT 'Stopped',
    startdate TIMESTAMP DEFAULT now()
);

INSERT INTO races (name) VALUES('default');

-- UPDATE teams SET laptime = EXTRACT(epoch FROM (now() - lastlap)), lastlap = now() WHERE teamname = '';

-- CREATE TABLE new_table AS TABLE teams WITH NO DATA;

-- alter sequence teams_id_seq restart with 1;
--  update teams set id = default;