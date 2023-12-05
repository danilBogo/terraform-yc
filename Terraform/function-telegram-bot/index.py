import os
import json
import requests
import ydb

telegram_token = os.getenv('TELEGRAM_TOKEN')
table = os.getenv('YDB_TABLE')
face_uri = os.getenv('FACE_URI')
photo_uri = os.getenv('PHOTO_URI')

driver = ydb.Driver(
    endpoint=os.getenv('YDB_ENDPOINT'),
    database=os.getenv('YDB_DATABASE'),
    credentials=ydb.iam.MetadataUrlCredentials(),
)

driver.wait(fail_fast=True, timeout=10)

pool = ydb.SessionPool(driver)

def get_face(session):
  query = f'''
    SELECT * FROM `{table}`
    WHERE `name` IS NULL
    LIMIT 1
    '''

  query = session.prepare(query)
  return session.transaction().execute(
    query,
    commit_tx=True,
    settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
  )

def set_name(session, name, telegram_file_id):
  query = f'''
    UPDATE `{table}`
    SET `name` = '{name}'
    WHERE `telegram_file_id` = '{telegram_file_id}'
    '''

  query = session.prepare(query)
  return session.transaction().execute(
    query,
    commit_tx=True,
    settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
  )

def set_telegram_file_id(session, key, telegram_file_id):
  query = f'''
    UPDATE `{table}`
    SET `telegram_file_id` = '{telegram_file_id}'
    WHERE `key` = '{key}'
    '''

  query = session.prepare(query)
  return session.transaction().execute(
    query,
    commit_tx=True,
    settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
  )

def find(session, name):
    query = f'''
        SELECT * FROM `{table}`
        WHERE `name` = '{name}'
        '''

    query = session.prepare(query)
    return session.transaction().execute(
        query,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )

def handler(event, context):
  body = json.loads(event["body"])
  print(f"BODY: {body}")
  try:
    message = body["message"]
  except:
    print(f"Invalid body: {body}")
    return None
  message_id = message["message_id"]
  chat_id = message["chat"]["id"]

  if "text" in message and message["text"] == '/getface':
      result = pool.retry_operation_sync(lambda session: get_face(session))[0]
      if len(result.rows) == 0:
          requests.get(
              url=f'https://api.telegram.org/bot{telegram_token}/sendMessage',
              params={
                  "chat_id": chat_id,
                  "text": "К сожалению нет лиц, у которых можно заполнить имя :(",
                  "reply_to_message_id": message_id
              }
          )
      else:
          key = result.rows[0].key
          name = result.rows[0].current_photo_name
          response = requests.post(
              url=f'https://api.telegram.org/bot{telegram_token}/sendPhoto',
              data={
                  "chat_id": chat_id,
                  "photo": f'{face_uri}/faces/{name}',
                  "reply_to_message_id": message_id
              }
          )

          telegram_file_id = json.loads(response.text)['result']['photo'][0]['file_id']
          print(f"telegram_file_id: {telegram_file_id}")
          print(f"key: {key}")
          pool.retry_operation_sync(lambda session: set_telegram_file_id(session, key, telegram_file_id))
  elif 'reply_to_message' in message and "photo" in message['reply_to_message'] and len(message['reply_to_message']["photo"]) > 0:
    telegram_file_id = message['reply_to_message']['photo'][0]['file_id']
    name = message['text']
    pool.retry_operation_sync(lambda session: set_name(session, name, telegram_file_id))
    requests.get(
        url=f'https://api.telegram.org/bot{telegram_token}/sendMessage',
        params={
            "chat_id": chat_id,
            "text": f"Название {name} было закреплено за данной фотографией",
            "reply_to_message_id": message_id
        }
    )
  elif "text" in message and message["text"].startswith('/find '):
      name = message["text"].split(" ", 1)[1]
      print(f"find {name}")
      result = pool.retry_operation_sync(lambda session: find(session, name))
      if len(result[0].rows) == 0:
          requests.get(
              url=f'https://api.telegram.org/bot{telegram_token}/sendMessage',
              params={
                  "chat_id": chat_id,
                  "text": f"Фотографий с {name} не найдены",
                  "reply_to_message_id": message_id
              }
          )
      else:
          links = [f'{photo_uri}/photos/{row.original_photo_name}' for row in result[0].rows]
          print(f"links {links}")
          media_group = json.dumps(
              [{"type": "photo", "media": link} for link in links]
          )

          requests.post(
              url=f'https://api.telegram.org/bot{telegram_token}/sendMediaGroup',
              data={
                  "chat_id": chat_id,
                  "media": media_group,
                  "reply_to_message_id": message_id
              }
          )
  else:
      requests.get(
          url=f'https://api.telegram.org/bot{telegram_token}/sendMessage',
          params={
              "chat_id": chat_id,
              "text": "Ошибка",
          }
      )

  return {
    "statusCode": 200
  }