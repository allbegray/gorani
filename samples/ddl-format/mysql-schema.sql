-- 쇼핑몰 스키마 (MySQL)
-- tables: 2

CREATE TABLE teams (
    id         bigint unsigned AUTO_INCREMENT PRIMARY KEY,
    name       varchar(100)    NOT NULL UNIQUE COMMENT '팀 이름',
    created_at datetime        DEFAULT CURRENT_TIMESTAMP NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE users (
    id         bigint unsigned           AUTO_INCREMENT PRIMARY KEY,
    team_id    bigint unsigned           NOT NULL,
    email      varchar(255)              NOT NULL UNIQUE,
    name       varchar(100)              NOT NULL,
    status     enum('active', 'blocked') DEFAULT 'active' NOT NULL,
    score      decimal(10, 2)            DEFAULT '0.00' NOT NULL CHECK (score >= 0),
    created_at datetime                  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT users_team_fkey FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE,
    KEY idx_users_team (team_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
