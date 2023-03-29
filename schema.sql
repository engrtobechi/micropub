CREATE TABLE users( id INT(11) AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                username VARCHAR(30) NOT NULL,
                password VARCHAR(100) NOT NULL,
                register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE articles( id INT(11) AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(100) NOT NULL,
                body TEXT NOT NULL,
                create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);