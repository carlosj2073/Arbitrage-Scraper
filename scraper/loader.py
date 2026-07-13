from logger import get_logger
import logging
import mysql.connector
import os
from dotenv import load_dotenv

class Loader:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

        db_config = {'host' : os.getenv('DB_HOST'),
                          'user' : os.getenv('DB_USER'),
                          'password' : os.getenv('DB_PASSWORD'),
                          'database' : os.getenv('DB_NAME')
        }
        self.db_connection = mysql.connector.connect(**db_config)
    
    def load_data(self, data: list[dict], website: str) -> None:
        cursor = self.db_connection.cursor()

        source_name = website
        cursor.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
        row = cursor.fetchone()
        if row:
            source_id = row[0]
        else:
            cursor.execute("INSERT INTO sources (name) VALUES (%s)", (source_name,))
            source_id = cursor.lastrowid
        
        try:
            for item in data:
                    
                    # Inserts into product_listings table
                    query = ("""
                        INSERT INTO product_listings (product_id, source_id, listing, brand, website_pid, url, image)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE website_pid = VALUES(website_pid), url = VALUES(url)
                    """)
                    values = item['product_id'], source_id, item['listing'], item['brand'], item.get('website_pid'), item.get('url'), item['image']
                    cursor.execute(query, values)
                    product_listings_id = cursor.lastrowid

                    # Inerts into price_scraped table
                    query = ("""
                        INSERT INTO price_scraped (product_listings_id, price_usd, scraped_at)
                        VALUES (%s, %s, NOW())
                    """)
                    values = (product_listings_id, item['price_usd'])
                    cursor.execute(query, values)
            self.db_connection.commit()

        except mysql.connector.Error as e:
            self.logger.error(f"Error inserting data into product_listings: {e}")
            self.db_connection.rollback()
        

        