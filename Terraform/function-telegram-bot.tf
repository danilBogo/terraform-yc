data "archive_file" "function_telegram_bot_zip" {
  output_path = "function-telegram-bot.zip"
  type        = "zip"
  source_dir  = "./function-telegram-bot"
}

resource "yandex_function" "telegram_bot" {
  name               = "${var.prefix}-${var.telegram_bot_name}"
  user_hash          = data.archive_file.function_telegram_bot_zip.output_base64sha256
  runtime            = "python312"
  entrypoint         = "index.handler"
  memory             = "128"
  execution_timeout  = "30"
  service_account_id = yandex_iam_service_account.sa_admin.id
  environment = {
    "TELEGRAM_TOKEN" : var.telegram_token
    "FACE_URI" : "https://${yandex_api_gateway.api_gateway.id}.apigw.yandexcloud.net"
    "PHOTO_URI" : "https://${yandex_api_gateway.api_gateway.id}.apigw.yandexcloud.net"
    "YDB_ENDPOINT" : "grpcs://${yandex_ydb_database_serverless.ydb_photo_face.ydb_api_endpoint}"
    "YDB_DATABASE" : yandex_ydb_database_serverless.ydb_photo_face.database_path
    "YDB_TABLE" : var.ydb_photo_face_table_name
  }
  content {
    zip_filename = data.archive_file.function_telegram_bot_zip.output_path
  }
}

resource "yandex_function_iam_binding" "telegram_bot_iam" {
  function_id = yandex_function.telegram_bot.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}

data "http" "telegram_bot_webhook" {
  url = "https://api.telegram.org/bot${var.telegram_token}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.telegram_bot.id}"
}