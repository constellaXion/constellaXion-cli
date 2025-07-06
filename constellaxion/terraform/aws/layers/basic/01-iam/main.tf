provider "aws" {
  region = var.region
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com", "ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "constellaxion_admin" {
  name               = "constellaxion-admin"
  description        = "Constellaxion Admin Role for deploying and training models"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

variable "managed_policy_arns" {
  type = set(string)
  default = [
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
  ]
}

resource "aws_iam_role_policy_attachment" "managed_policies" {
  for_each = var.managed_policy_arns

  role       = aws_iam_role.constellaxion_admin.name
  policy_arn = each.value
}

resource "aws_iam_role_policy" "ecr_inline_policy" {
  name = "ConstellaxionECRAccess"
  role = aws_iam_role.constellaxion_admin.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
