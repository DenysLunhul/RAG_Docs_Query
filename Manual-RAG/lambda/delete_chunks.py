import os
import pg8000


def lambda_handler(event, context):
    conn = pg8000.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ['DB_PORT']),
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )

    for record in event['Records']:
        filename = record['s3']['object']['key']
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_chunks WHERE filename = %s", (filename,))
        conn.commit()
        cursor.close()

    conn.close()
    return {'statusCode': 200, 'body': 'Chunks deleted'}
