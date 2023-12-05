resource "yandex_storage_bucket" "s3_faces" {
  bucket     = "${var.prefix}-${var.s3_faces_name}"
  access_key = yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_admin_static_access_keys.secret_key
  max_size   = 5368709120
  anonymous_access_flags {
    read = false
    list = false
  }
}