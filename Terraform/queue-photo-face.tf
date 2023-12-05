resource "yandex_message_queue" "queue_photo_face" {
  name       = "${var.prefix}-${var.queue_photo_face_name}"
  access_key = yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.secret_key
}