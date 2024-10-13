import logging
import psycopg2
logger = logging.getLogger(__name__)

class DbService:
    def connect(self, host, dbName, user):
        try:
            connection = psycopg2.connect(f'host={host} dbname={dbName} user={user}')
            connection.autocommit = True  
            logger.info("Connection to the database was successful")
            return connection
        except Exception as e:
            logger.info(f"An error occurred when trying to connect to db: {e}")
            return None
    
    def check_db_existence(self, dbConnection, dbName):
        try:
            with dbConnection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (dbName,))
                exists = cursor.fetchone() is not None
                logger.info(f"Database {'exists' if exists else "does not exist"}")
                return exists
        except Exception as e:
            logger.info(f"Error checking database existence: {e}")
            return None
    
    def create_database(self, dbConnection, dbName):
        try:
            with dbConnection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                logger.info(f"Creating database {dbName}")
        except Exception as e:
            logger.info(f"Error creating {dbName} database: {e}")
            return None
    
    def enable_vector_extension(self, dbConnection):
        try:
            with dbConnection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info(f"Enabling vector extension in db")
        except Exception as e:
            logger.info(f"Error enabling vector extension in db: {e}")
            return None
    
    def create_embeddings_table(self, dbConnection):
        try:
            with dbConnection.cursor() as cursor:
                table_create_command = """
                CREATE TABLE IF NOT EXISTS text_embeddings (
                    id SERIAL PRIMARY KEY,
                    text TEXT,
                    embedding VECTOR(384)
                    )
                """
                cursor.execute(table_create_command)
        except Exception as e:
            logger.info(f"Error creating embeddings table: {e}")
            return None
        
    def clean_embeddings_table(self, dbConnection):
        try:
            with dbConnection.cursor() as cursor:
                table_clean_command = """
                truncate table text_embeddings
                """
                cursor.execute(table_clean_command)
        except Exception as e:
            logger.info(f"Error cleaning embeddings table: {e}")
            return None
        
    def store_embedding(self, dbConnection, original_text, embedding):
        sql_query = """
        INSERT INTO text_embeddings (text, embedding)
        VALUES (%s, %s)
        """

        with dbConnection.cursor() as cursor:
        # chunks = chunk_text(text)
        
        # for chunk in chunks:
        #     embedding = get_embedding(chunk)
            cursor.execute(sql_query, (original_text, embedding.tolist()))


    def close_connection(self, dbConnection):
        try:
            dbConnection.close()
        except Exception as e:
            logger.info(f"Error closing db connection: {e}")
            return None

        

            

