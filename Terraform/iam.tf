resource "yandex_iam_service_account" "sa_admin" {
  folder_id = var.folder_id
  name      = "sa-${var.prefix}-admin"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_admin_grant" {
  folder_id = var.folder_id
  role      = "admin"
  member    = "serviceAccount:${yandex_iam_service_account.sa_admin.id}"
}

resource "yandex_iam_service_account_static_access_key" "sa_admin_static_access_keys" {
  service_account_id = yandex_iam_service_account.sa_admin.id
}

resource "yandex_iam_service_account_api_key" "sa_admin_api_key" {
  service_account_id = yandex_iam_service_account.sa_admin.id
}