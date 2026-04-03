# ── Self-Healing Pipeline Agent — Infrastructure as Code ──
# Terraform configuration for AWS deployment

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

variable "zhipuai_api_key" {
  sensitive = true
}

# ── VPC & Networking ────────────────────────────────────
resource "aws_vpc" "pipeline_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name        = "pipeline-agent-vpc-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.pipeline_vpc.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = "${var.aws_region}${count.index == 0 ? "a" : "b"}"

  tags = {
    Name = "pipeline-public-${count.index + 1}"
  }
}

# ── ECS Cluster (Fargate) ──────────────────────────────
resource "aws_ecs_cluster" "pipeline_cluster" {
  name = "pipeline-agent-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ── Secrets Manager ────────────────────────────────────
resource "aws_secretsmanager_secret" "api_key" {
  name = "pipeline-agent/zhipuai-api-key"
}

resource "aws_secretsmanager_secret_version" "api_key" {
  secret_id     = aws_secretsmanager_secret.api_key.id
  secret_string = var.zhipuai_api_key
}

# ── S3 Bucket (Pipeline Artifacts) ─────────────────────
resource "aws_s3_bucket" "artifacts" {
  bucket = "pipeline-agent-artifacts-${var.environment}"
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    expiration {
      days = 365
    }
  }
}

# ── CloudWatch Log Group ───────────────────────────────
resource "aws_cloudwatch_log_group" "pipeline_logs" {
  name              = "/pipeline-agent/${var.environment}"
  retention_in_days = 30
}

# ── CloudWatch Alarms ──────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "pipeline-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorCount"
  namespace           = "PipelineAgent"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Pipeline error rate is too high"
}

# ── Outputs ────────────────────────────────────────────
output "cluster_name" {
  value = aws_ecs_cluster.pipeline_cluster.name
}

output "artifacts_bucket" {
  value = aws_s3_bucket.artifacts.id
}

output "log_group" {
  value = aws_cloudwatch_log_group.pipeline_logs.name
}
