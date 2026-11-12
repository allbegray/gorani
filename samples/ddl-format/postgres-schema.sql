-- 쇼핑몰 스키마
-- tables: 4

CREATE TYPE user_status AS ENUM ('active', 'blocked', 'pending');

CREATE TABLE audit_log (
    id         bigint       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id   bigint,
    action     text         NOT NULL,
    payload    jsonb,
    created_at timestamp(6) DEFAULT now()
);

CREATE TABLE teams (
    id         bigserial    PRIMARY KEY,
    name       varchar(100) NOT NULL,
    created_at timestamptz  DEFAULT now() NOT NULL
);

COMMENT ON TABLE teams IS '팀';
COMMENT ON COLUMN teams.name IS '팀 이름';

CREATE TABLE users (
    id         bigserial      PRIMARY KEY,
    email      varchar(255)   NOT NULL UNIQUE,
    name       varchar(100)   NOT NULL,
    team_id    bigint         NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    status     user_status    DEFAULT 'active' NOT NULL,
    score      numeric(10, 2) DEFAULT 0 NOT NULL CHECK (score >= 0),
    created_at timestamptz    DEFAULT now() NOT NULL
);

COMMENT ON TABLE users IS '사용자';
COMMENT ON COLUMN users.email IS '로그인 이메일';

CREATE INDEX idx_users_lower_email ON users (lower(email));
CREATE INDEX idx_users_team ON users (team_id);
CREATE UNIQUE INDEX uq_users_name_team ON users (name, team_id) WHERE team_id > 0;

CREATE TABLE projects (
    id       bigserial    PRIMARY KEY,
    owner_id bigint       NOT NULL REFERENCES users (id),
    slug     varchar(80)  NOT NULL UNIQUE,
    title    varchar(200) NOT NULL
);
