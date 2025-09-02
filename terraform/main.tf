provider "aws" {
  region = "us-east-1"
}

resource "aws_ecs_cluster" "valuation_cluster" {
  name = "valuation-engine-cluster"
}

resource "aws_ecs_task_definition" "valuation_task" {
  family                   = "valuation-engine"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole"

  container_definitions = <<DEFINITION
[
  {
    "name": "valuation-engine",
    "image": "your-dockerhub-username/valuation-engine:latest",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 8000,
        "hostPort": 8000
      }
    ]
  }
]
DEFINITION
}

resource "aws_ecs_service" "valuation_service" {
  name            = "valuation-service"
  cluster         = aws_ecs_cluster.valuation_cluster.id
  task_definition = aws_ecs_task_definition.valuation_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = ["subnet-abc123"]
    assign_public_ip = true
  }
}
