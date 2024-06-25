CREATE TABLE notifications (
    id INTEGER,
    webhook_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY(id AUTOINCREMENT)
);

CREATE TABLE archived_notifications (
    id INTEGER,
    webhook_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY(id AUTOINCREMENT)
);

CREATE TABLE failed_notifications (
    id INTEGER,
    webhook_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    error TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY(id AUTOINCREMENT)
);
