import os
import uuid

import psycopg2.pool

from utils import jsondumps

# Allow initialization in a lazy way
pool = psycopg2.pool.SimpleConnectionPool(
    1, 8,  # min and max connections
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
)


def create_db_record(content, embedding):
    id_ = str(uuid.uuid4())
    conn = pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO knowledgebase (id, content, embedding)
            VALUES (%s, %s, %s)''',
            (id_, content, jsondumps(embedding))
        )
        conn.commit()
    finally:
        cursor.close()
        pool.putconn(conn)
    return id_


def get_db_records_by_embedding(embedding, limit=5):
    conn = pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT
                id,
                content,
                embedding <-> %s AS distance
            FROM knowledgebase
            ORDER BY distance ASC
            LIMIT %s''', (jsondumps(embedding), limit))
        results = cursor.fetchall()
    finally:
        cursor.close()
        pool.putconn(conn)

    return [
        {
            'id': result[0],
            'content': result[1]
        }
        for result in results
    ]
