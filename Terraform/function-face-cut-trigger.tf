resource "yandex_function_trigger" "function_face_cut_trigger" {
  name = "${var.prefix}-${var.function_face_cut_trigger_name}"
  message_queue {
    queue_id           = yandex_message_queue.queue_photo_face.arn
    service_account_id = yandex_iam_service_account.sa_admin.id
    batch_cutoff       = "0"
    batch_size         = "1"
  }
  function {
    id                 = yandex_function.function_face_cut.id
    service_account_id = yandex_iam_service_account.sa_admin.id
  }
}