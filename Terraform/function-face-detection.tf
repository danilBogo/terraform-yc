data "archive_file" "function_face_detection_zip" {
  output_path = "function-face-detection.zip"
  type        = "zip"
  source_dir  = "./function-face-detection"
}

resource "yandex_function" "function_face_detection" {
  name               = "${var.prefix}-${var.function_face_detection_name}"
  user_hash          = data.archive_file.function_face_detection_zip.output_base64sha256
  runtime            = "python312"
  entrypoint         = "index.handler"
  memory             = "128"
  execution_timeout  = "30"
  service_account_id = yandex_iam_service_account.sa_admin.id
  environment = {
    "API_KEY" : yandex_iam_service_account_api_key.sa_admin_api_key.secret_key
    "FOLDER_ID" : var.folder_id
    "STORAGE_BASE_URI" : var.storage_base_uri
    "VISION_API_URI" : var.vision_api_uri
    "QUEUE_BASE_URI" : var.queue_base_uri
    "ACCESS_KEY" : yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.access_key
    "SECRET_KEY" : yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.secret_key
    "QUEUE_NAME" : "${var.prefix}-${var.queue_photo_face_name}"
    "ZONE" : var.zone
  }
  content {
    zip_filename = data.archive_file.function_face_detection_zip.output_path
  }
}