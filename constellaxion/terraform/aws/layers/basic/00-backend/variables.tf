variable "region" {
  type        = string
  description = "The AWS region where resources will be created."
}

variable "bucket_name" {
  type        = string
  description = "The deterministic, unique name for the S3 backend bucket."
}

variable "enable_dynamodb_locking" {
  type        = bool
  description = "If true, a DynamoDB table will be created for state locking."
  default     = true
}
