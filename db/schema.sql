# Arbritage Pipeline Schema Architecture v1

CREATE DATABASE price_arbritage;
USE price_arbritage;
	
CREATE TABLE IF NOT EXISTS sources(
	id INT PRIMARY KEY AUTO_INCREMENT,
	name VARCHAR(30) UNIQUE
);

CREATE TABLE IF NOT EXISTS products(
	id INT PRIMARY KEY AUTO_INCREMENT,
	title VARCHAR(300) UNIQUE NOT NULL,
	is_matched ENUM('matched','unmatched','partial') DEFAULT 'unmatched' NOT NULL
	# (DEFAULT + NOT NULL) mitigates NULL ingestion
);

CREATE TABLE IF NOT EXISTS product_listings(
	id INT PRIMARY KEY AUTO_INCREMENT,
	product_id INT, # NULLS are necessary for data integrity of unmatched listings
	source_id INT NOT NULL,
	listing TEXT NOT NULL,
	brand VARCHAR (60),
	website_pid VARCHAR(60) UNIQUE,
	url VARCHAR(500) UNIQUE,
	image JSON,
	FOREIGN KEY (product_id) REFERENCES products(id),
	FOREIGN KEY (source_id) REFERENCES sources(id),
	INDEX idx_url (url) # For deduplication on url
);

CREATE TABLE IF NOT EXISTS price_scraped(
	id INT PRIMARY KEY AUTO_INCREMENT,
	product_listings_id INT NOT NULL,
	price_usd DECIMAL(10,2) NOT NULL,
	scraped_at DATETIME NOT NULL,
	FOREIGN KEY (product_listings_id) REFERENCES product_listings(id) ON DELETE CASCADE
);



SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'price_arbritage'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
