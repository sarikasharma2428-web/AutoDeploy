.PHONY: help install dev build test lint deploy clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development environment"
	@echo "  make build        - Build Docker images"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make deploy       - Deploy to production"
	@echo "  make clean        - Clean up resources"

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker-compose up -d
	. venv/bin/activate && uvicorn app:app --reload &
	cd frontend && npm run dev

build:
	docker build -f docker/Dockerfile.backend -t repo-analyzer-backend:latest .
	docker build -f docker/Dockerfile.frontend -t repo-analyzer-frontend:latest .

test:
	. venv/bin/activate && pytest tests/ -v
	cd frontend && npm run test

lint:
	. venv/bin/activate && black . && flake8 .
	cd frontend && npm run lint

deploy:
	./scripts/deploy.sh prod latest

deploy-dev:
	./scripts/deploy.sh dev latest

backup:
	./scripts/backup.sh

health:
	./scripts/check-health.sh

monitoring:
	./scripts/setup-monitoring.sh

clean:
	docker-compose down -v
	rm -rf venv frontend/node_modules frontend/dist
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

k8s-apply:
	kubectl apply -k k8s/base/

k8s-delete:
	kubectl delete -k k8s/base/

terraform-init:
	cd terraform && terraform init

terraform-plan:
	cd terraform && terraform plan

terraform-apply:
	cd terraform && terraform apply

terraform-destroy:
	cd terraform && terraform destroy
