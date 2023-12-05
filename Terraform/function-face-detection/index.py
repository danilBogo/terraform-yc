import requests
import os
import base64
import boto3
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
        ExpiresIn=60
    )

    print(f"URL: {url}")

    return url


def detect_faces(vision_api_uri, api_key, folder_id, image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        image_data = response.content
        base64_encoded_image = base64.b64encode(image_data).decode('utf-8')

        body = {
            "analyzeSpecs": [
                {
                    "features": [
                        {
                            "type": "FACE_DETECTION",
                            "maxResults": 5
                        }
                    ],
                    "mimeType": "image/jpeg",
                    "content": base64_encoded_image
                }
            ],
            "folderId": folder_id
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {api_key}",
        }

        response = requests.post(vision_api_uri, headers=headers, data=json.dumps(body))


        if response.status_code == 200:
            result = response.json()
            print(f"RESULT: {result}")
            faces = result['results'][0]['results'][0]['faceDetection']['faces']
            return faces
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

    else:
        print(f"Failed to fetch the image. Status code: {response.status_code}")
        return None


def get_queue(host_url, access_key, secret_key, zone, queue_url):
    session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    queue = session.resource(
        service_name='sqs',
        endpoint_url = host_url,
        region_name=zone
    ).Queue(queue_url)

    return queue


def process_face(queue_base_uri, queue_name, access_key, secret_key, zone, data):
    queue_url = get_queue_url(queue_base_uri, queue_name, access_key, secret_key, zone)
    send_face_to_queue(queue_base_uri, access_key, secret_key, zone, queue_url, data)

def get_queue_url(queue_base_uri, queue_name, access_key, secret_key, zone):
    sqs = boto3.client(
        'sqs',
        endpoint_url=queue_base_uri,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=zone
    )

    response = sqs.get_queue_url(QueueName=queue_name)

    queue_url = response['QueueUrl']

    return queue_url

def send_face_to_queue(queue_base_uri, access_key, secret_key, zone, queue_url, data):
    queue = get_queue(queue_base_uri, access_key, secret_key, zone, queue_url)
    queue.send_message(MessageBody=json.dumps(data))
    print(f"Published to queue: {data}")

def get_data(coordinates, object_id):
    return {
    "key": object_id,
    "coordinates": coordinates
}

def handler(event, context):
    details = event['messages'][0]['details']
    bucket_id = details['bucket_id']
    object_id = details['object_id']

    api_key = os.getenv('API_KEY')
    folder_id = os.getenv('FOLDER_ID')
    access_key = os.getenv('ACCESS_KEY')
    secret_key = os.getenv('SECRET_KEY')
    storage_base_uri = os.getenv('STORAGE_BASE_URI')
    vision_api_uri = os.getenv('VISION_API_URI')
    queue_base_uri = os.getenv('QUEUE_BASE_URI')
    queue_name = os.getenv('QUEUE_NAME')
    zone = os.getenv('ZONE').replace('-a', '')

    image_url = get_image_url(storage_base_uri, access_key, secret_key, bucket_id, object_id)

    faces = detect_faces(vision_api_uri, api_key, folder_id, image_url)

    if faces:
        print(f"Найдено {len(faces)} лиц:")
        for idx, face in enumerate(faces, 1):
            print(f"Лицо id {idx}:")
            print(f"  Координаты: {face['boundingBox']['vertices']}")
            data = get_data(face['boundingBox']['vertices'], object_id)
            process_face(queue_base_uri, queue_name, access_key, secret_key, zone, data)

    else:
        print("Не удалось обнаружить лица.")