output "alb_dns_name" {
  description = "Public DNS of Application Load Balancer"
  value       = aws_lb.alb.dns_name
}

output "backend_url" {
  description = "Public URL for OpenAI-compatible API"
  value       = "http://${aws_lb.alb.dns_name}:8000"
}

output "frontend_url" {
  description = "Public URL for Web Dashboard & Chat Playground"
  value       = "http://${aws_lb.alb.dns_name}"
}

output "ecr_backend_repo" {
  description = "ECR Repository URL for Backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repo" {
  description = "ECR Repository URL for Frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "rds_endpoint" {
  description = "PostgreSQL Database Host"
  value       = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  description = "Redis Cache Host"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}
