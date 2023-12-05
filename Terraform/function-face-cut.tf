data "archive_file" "function_face_cut_zip" {
  output_path = "function-face-cut.zip"
  type        = "zip"
  source_dir  = "./function-face-cut"
}

resource "yandex_function" "function_face_cut" {
  name               = "${var.prefix}-${var.function_face_cut_name}"
  user_hash          = data.archive_file.function_face_cut_zip.output_base64sha256
  runtime            = "python312"
  entrypoint         = "index.handler"
  memory             = "128"
  execution_timeout  = "30"
  service_account_id = yandex_iam_service_account.sa_admin.id
  environment = {
    "PHOTOS_BUCKED_ID" = yandex_storage_bucket.s3_photos.id
    "FACES_BUCKED_ID"  = yandex_storage_bucket.s3_faces.id
    "STORAGE_BASE_URI" : var.storage_base_uri
    "ACCESS_KEY" : yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.access_key
    "SECRET_KEY" : yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.secret_key
    "ZONE" : var.zone
    "YDB_ENDPOINT" : "grpcs://${yandex_ydb_database_serverless.ydb_photo_face.ydb_api_endpoint}"
    "YDB_DATABASE" : yandex_ydb_database_serverless.ydb_photo_face.database_path
    "YDB_TABLE" : var.ydb_photo_face_table_name
  }
  content {
    zip_filename = data.archive_file.function_face_cut_zip.output_path
  }
}