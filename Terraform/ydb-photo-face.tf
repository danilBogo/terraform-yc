resource "yandex_ydb_database_serverless" "ydb_photo_face" {
  name                = "${var.prefix}-${var.ydb_photo_face_name}"
  deletion_protection = "true"

  serverless_database {
    storage_size_limit = 5
  }
}

resource "yandex_ydb_table" "ydb_photo_face_table" {
  path              = var.ydb_photo_face_table_name
  connection_string = yandex_ydb_database_serverless.ydb_photo_face.ydb_full_endpoint
  primary_key       = ["key"]

  column {
    name     = "key"
    type     = "Utf8"
    not_null = true
  }

  column {
    name = "name"
    type = "Utf8"
  }

  column {
    name = "original_photo_name"
    type = "Utf8"
  }

  column {
    name = "original_photo_bucket_id"
    type = "Utf8"
  }

  column {
    name = "current_photo_name"
    type = "Utf8"
  }

  column {
    name = "current_photo_bucket_id"
    type = "Utf8"
  }

  column {
    name = "telegram_file_id"
    type = "Utf8"
  }
}