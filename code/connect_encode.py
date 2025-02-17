import argparse
import psycopg2
import time


def _create_db_connection():
        """Create and return a database connection."""
        return psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port = 15432
        )

def initialize_database(conn):
    """Initialize the database with required extensions and tables."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS aidb CASCADE;")
        cur.execute("DROP TABLE IF EXISTS products;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                img_id TEXT,
                gender VARCHAR(50),
                masterCategory VARCHAR(100),
                subCategory VARCHAR(100),
                articleType VARCHAR(100),
                baseColour VARCHAR(50),
                season TEXT,
                year INTEGER,
                usage TEXT NULL,
                productDisplayName TEXT NULL
            );
        """)

def create_and_refresh_retriever(conn, retriever_name, s3_bucket_name, s3_endpoint):
    """Create and refresh the S3 retriever."""
    
    with conn.cursor() as cur:
        start_time = time.time()
        cur.execute(f"""
            SELECT aidb.create_s3_retriever(
                '{retriever_name}',
                'public', 
                'clip-vit-base-patch32',
                'img',
                '{s3_bucket_name}',
                '',
                '{s3_endpoint}'
            );
        """)
        cur.execute("SELECT aidb.refresh_retriever('img_embeddings');")
        vector_time = time.time() - start_time
        print(f"Creating and refreshing retriever took {vector_time:.4f} seconds.")

def load_data_to_db(conn, file_path):
    """Load data from CSV file to the database."""
    with open(file_path, 'r') as f:
        next(f)  # Skip the header row
        with conn.cursor() as cur:
            cur.copy_expert("COPY products FROM STDIN WITH CSV HEADER", f)
    f.close()


def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("retriever_name", help="enter your retriever name", type=str)
        parser.add_argument("s3_bucket_name", help="enter your s3 bucket name", type=str)
        parser.add_argument("--s3_endpoint", help="enter your s3 endpoint leave blank if your bucket is not public", type=str, default='')
        args = parser.parse_args()

        try:
                conn = _create_db_connection()
                conn.autocommit = True  # Enable autocommit for creating the database
                start_time = time.time()
                initialize_database(conn)
                create_and_refresh_retriever(conn, args.retriever_name, args.s3_bucket_name, args.s3_endpoint)
                # load_data_to_db(conn, 'dataset/stylesc.csv')
                vector_time = time.time() - start_time
                print(f"Total process time: {vector_time:.4f} seconds.")
        except (Exception, psycopg2.DatabaseError) as error:
                print(f"Error: {error}")
        finally:
                if conn:
                        conn.close()

if __name__ == "__main__":
    main()