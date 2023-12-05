import os
import boto3
from PIL import Image
import requests
from io import BytesIO
import uuid
import ydb
import json


def get_image_url(storage_base_uri, access_key, secret_key, bucket_id, object_id):
    s3 = boto3.client(
        's3',
        endpoint_url=storage_base_uri,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_id,
            'Key': object_id,
        },
        ExpiresIn=3600
    )

    print(f"URL: {url}")

    return url


storage_base_uri = os.getenv('STORAGE_BASE_URI')
access_key = os.getenv('ACCESS_KEY')
secret_key = os.getenv('SECRET_KEY')
photos_bucked_id = os.getenv('PHOTOS_BUCKED_ID')
faces_bucked_id = os.getenv('FACES_BUCKED_ID')
zone = os.getenv('ZONE').replace('-a', '')
endpoint = os.getenv('YDB_ENDPOINT')
database = os.getenv('YDB_DATABASE')
table = os.getenv('YDB_TABLE')


def get_cropped_image(message):
    object_id = message['key']

    image_url = get_image_url(storage_base_uri, access_key, secret_key, photos_bucked_id, object_id)
    print(image_url)

    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    coordinates = [(int(coord['x']), int(coord['y'])) for coord in message['coordinates']]

    x_values = [coord[0] for coord in coordinates]
    y_values = [coord[1] for coord in coordinates]

    left = min(x_values)
    top = min(y_values)
    right = max(x_values)
    bottom = max(y_values)
    print(f"Cropped coordinates {(left, top, right, bottom)}")

    cropped_img = img.crop((left, top, right, bottom))

    return cropped_img


def insert_data(session, original_photo_name, original_photo_bucket_id, current_photo_name, current_photo_bucket_id):
    query = f'''
            DECLARE $key AS Utf8;
            DECLARE $original_photo_name AS Utf8;
            DECLARE $original_photo_bucket_id AS Utf8;
            DECLARE $current_photo_name AS Utf8;
            DECLARE $current_photo_bucket_id AS Utf8;

            UPSERT INTO `{os.getenv('YDB_TABLE')}` (
                `key`,
                `original_photo_name`,
                `original_photo_bucket_id`,
                `current_photo_name`,
                `current_photo_bucket_id`
            )
            VALUES (
                $key,
                $original_photo_name,
                $original_photo_bucket_id,
                $current_photo_name,
                $current_photo_bucket_id
            )
            '''

    params = {
        '$key': str(uuid.uuid4()),
        '$original_photo_name': original_photo_name,
        '$original_photo_bucket_id': original_photo_bucket_id,
        '$current_photo_name': current_photo_name,
        '$current_photo_bucket_id': current_photo_bucket_id
    }

    query = session.prepare(query)
    return session.transaction().execute(
        query,
        params,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )


def save_to_ydb(original_photo_name, original_photo_bucket_id, current_photo_name, current_photo_bucket_id):
    driver = ydb.Driver(
        endpoint=os.getenv('YDB_ENDPOINT'),
        database=os.getenv('YDB_DATABASE'),
        credentials=ydb.iam.MetadataUrlCredentials(),
    )

    driver.wait(fail_fast=True, timeout=10)

    pool = ydb.SessionPool(driver)

    pool.retry_operation_sync(lambda session: insert_data(session, original_photo_name, original_photo_bucket_id, current_photo_name, current_photo_bucket_id))


def process_message(message):
    print(message)
    cropped_image = get_cropped_image(message)
    cropped_image_name = f"{uuid.uuid4()}.jpg"

    s3 = boto3.client(
        's3',
        endpoint_url=storage_base_uri,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=zone
    )

    with BytesIO() as data:
        cropped_image.save(data, format='JPEG')
        data.seek(0)
        s3.upload_fileobj(data, faces_bucked_id, cropped_image_name)

    cropped_image_url = get_image_url(storage_base_uri, access_key, secret_key, faces_bucked_id, cropped_image_name)
    print(f"Image {cropped_image_name} saved with url {cropped_image_url}")

    save_to_ydb(message['key'], photos_bucked_id, cropped_image_name, faces_bucked_id)


def handler(event, context):
    for message in event['messages']:
        print(f'Process message {message}')
        json_body = message['details']['message']['body']
        message = json.loads(json_body)
        process_message(message)
