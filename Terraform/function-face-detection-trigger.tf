resource "yandex_function_trigger" "function_face_detection_trigger" {
  name = "${var.prefix}-${var.function_face_detection_trigger_name}"
  object_storage {
    bucket_id    = yandex_storage_bucket.s3_photos.id
    create       = true
    delete       = false
    update       = false
    suffix       = ".jpg"
    batch_cutoff = ""
  }
  function {
    id                 = yandex_function.function_face_detection.id
    service_account_id = yandex_iam_service_account.sa_admin.id
  }
}