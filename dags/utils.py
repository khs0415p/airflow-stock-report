import logging
import MySQLdb
import os



HOST = os.environ.get("MYSQL_HOST")
USER = "root"
PORT = os.environ.get("MYSQL_PORT", 3306)
PASSWORD = os.environ.get("MYSQL_ROOT_PASSWORD", "root")
DATABASE = os.environ.get("MYSQL_DATABASE", 'crawling')


class CustomMysql:
    def __init__(self):
        
        self.db_conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, password=PASSWORD)
    
    
    def check_database_exitsts(self, db_name="crawling"):
        db_cursor = self.db_conn.cursor()
        query = f"""SHOW DATABASES LIKE '{db_name}'"""
        db_cursor.execute(query)
        result = db_cursor.fetchall()
        if result:
            return True
        return False
    
        
    def create_database(self, db_name="crawling"):
        db_cursor = self.db_conn.cursor()
        query = f"CREATE DATABASE {db_name}"
        db_cursor.execute(query)
        logging.info(f"Create : {db_name} Database")
    

    def set_database(self):
        self.crawl_conn =  MySQLdb.connect(host=HOST, port=PORT, user=USER,
                    password=PASSWORD, database=DATABASE)


    def check_table_exists(self, table_name):
        db_cursor = self.crawl_conn.cursor()
        query = f"SHOW TABLES LIKE '{table_name}'"
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        if result:
            return True
        return False


    def create_table(self, table_name, query):
        db_cursor = self.crawl_conn.cursor()
        db_cursor.execute(query)
        logging.info(f"Create : {table_name} Table")
    

def db_check():
    db_cls = CustomMysql()
    if not db_cls.check_database_exitsts():
        db_cls.create_database()
    db_cls.set_database()
    
    if not db_cls.check_table_exists(table_name='tickers'):
        query = "CREATE TABLE tickers \
                (name VARCHAR(25) NOT NULL PRIMARY KEY, \
                code CHAR(7)  NOT NULL)"
        db_cls.create_table('tickers', query)

    if not db_cls.check_table_exists(table_name='stock'):
        query = "CREATE TABLE stock \
            (id INT(5) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,\
            reporting_date DATE, \
            provider VARCHAR(25), \
            analyst VARCHAR(10), \
            name VARCHAR(25), \
            close_price VARCHAR(25)  NOT NULL, \
            target_price VARCHAR(25)  NOT NULL, \
            opinion VARCHAR(25)  NOT NULL, \
            title VARCHAR(255), \
            FOREIGN KEY(name) REFERENCES tickers(name) ON DELETE CASCADE ON UPDATE CASCADE,\
            INDEX date_index (reporting_date))"
        db_cls.create_table('stock', query)
    
    db_cls.crawl_conn.close()
    db_cls.db_conn.close()
    