resource "yandex_api_gateway" "api_gateway" {
  name = "${var.prefix}-${var.api_gateway_name}"
  spec = <<-EOT
      openapi: "3.0.0"
      info:
        version: 1.0.0
        title: API
      paths:
        /photos/{photo_id}:
          get:
            parameters:
              - name: photo_id
                in: path
                required: true
                schema:
                  type: string
            x-yc-apigateway-integration:
              type: object_storage
              bucket: ${yandex_storage_bucket.s3_photos.id}
              object: '{photo_id}'
              error_object: error.html
              service_account_id: ${yandex_iam_service_account.sa_admin.id}
        /faces/{face_id}:
          get:
            parameters:
              - name: face_id
                in: path
                required: true
                schema:
                  type: string
            x-yc-apigateway-integration:
              type: object_storage
              bucket: ${yandex_storage_bucket.s3_faces.id}
              object: '{face_id}'
              error_object: error.html
              service_account_id: ${yandex_iam_service_account.sa_admin.id}
  EOT
}