CREATE TABLE teams (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE teams IS '팀';
COMMENT ON COLUMN teams.name IS '팀 이름';

CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'blocked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS '사용자';
COMMENT ON COLUMN users.email IS '로그인 이메일';
COMMENT ON COLUMN users.team_id IS '소속 팀';

CREATE INDEX idx_users_team ON users(team_id);

ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;
COMMENT ON COLUMN users.last_login_at IS '마지막 로그인';

CREATE TABLE projects (
  id BIGSERIAL PRIMARY KEY,
  owner_id BIGINT NOT NULL,
  slug VARCHAR(80) NOT NULL,
  title VARCHAR(200) NOT NULL,
  CONSTRAINT uq_projects_slug UNIQUE (slug),
  CONSTRAINT fk_projects_owner FOREIGN KEY (owner_id) REFERENCES users(id)
);

COMMENT ON TABLE projects IS '프로젝트';
COMMENT ON COLUMN projects.slug IS 'URL slug';
COMMENT ON COLUMN projects.owner_id IS '소유자';
