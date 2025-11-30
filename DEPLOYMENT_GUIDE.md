Deployment Guide – Recruiting SaaS Platform

This document explains how to deploy the Recruiting SaaS Platform to multiple environments:

Local production simulation (Docker Compose)

Single-server VM (EC2, DigitalOcean, etc.)

AWS App Runner (easiest managed option)

AWS ECS Fargate

Kubernetes (EKS, GKE, AKS)

It also covers:

SSL/TLS setup

Environment variables (secrets)

Database configuration

WSS support for Streamlit

Scaling and observability

Backups & DR

1. Overview of Deployment Architecture

Deployment architecture consists of:

1. Backend (FastAPI)

Exposed port: 8000

Runs behind reverse proxy / load balancer

Requires:

Python dependencies

Environment variables in .env

Persistent database (SQLite for dev; Postgres recommended for production)

2. Frontend (Streamlit)

Exposed port: 8501

Communicates with backend via REST JSON

Requires WSS compatibility for Streamlit WebSocket connections

3. Database

Local SQLite for dev

PostgreSQL recommended in production

Render PostgreSQL

RDS (AWS)

Supabase

Neon DB (serverless)

2. Environment Variables

Copy .env.example → .env:

SECRET_KEY=CHANGE_ME

SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db
# For Postgres production use:
# SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME

BACKEND_CORS_ORIGINS=http://localhost:8501

OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini

MATCHING_USE_OPENAI=false


These must be injected into production environment using:

AWS SSM Parameter Store

Docker Compose .env

ECS task definition environment

Kubernetes Secrets

App Runner encrypted environment vars

3. Local Production Simulation (Docker Compose)

Recommended before deploying anywhere.

Inside infra/docker-compose.yml:

docker-compose -f infra/docker-compose.yml up --build


This will start:

Service	URL
FastAPI backend	http://localhost:8000

Backend docs	http://localhost:8000/docs

Streamlit frontend	http://localhost:8501
Stopping services:
docker-compose down

Running in detached mode:
docker-compose up -d

4. Deploying to a Single VM (Ubuntu / EC2 / DigitalOcean)
4.1 Install dependencies
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl enable docker --now

4.2 Clone repository
git clone https://github.com/your-org/recruiting-platform.git
cd recruiting-platform

4.3 Configure .env
nano .env


Use Postgres (recommended):

SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/db

4.4 Run with Docker Compose
docker-compose -f infra/docker-compose.yml up -d --build

4.5 Add reverse proxy for SSL

Use Nginx or Caddy.

Nginx example:

Domain for frontend: app.mycompany.com

Domain for backend: api.mycompany.com

server {
    listen 80;
    server_name app.mycompany.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}


Then use Certbot:

sudo certbot --nginx -d app.mycompany.com

Important — Streamlit HTTPS/WSS

Streamlit requires WSS over port 443 for WebSocket communication.

Ensure your proxy includes:

proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

5. Deploying on AWS App Runner (Easiest Managed Deployment)

Best option if you want zero infrastructure.

5.1 Containerize Backend

Use infra/Dockerfile.backend.

Push to ECR:

aws ecr create-repository --repository-name recruiting-backend
docker build -t recruiting-backend -f infra/Dockerfile.backend .
docker tag recruiting-backend:latest <ECR_URL>/recruiting-backend:latest
docker push <ECR_URL>/recruiting-backend:latest

5.2 Deploy Backend to App Runner

Go to AWS App Runner

“Deploy from ECR”

Set port = 8000

Add environment variables (copy .env)

Your backend is now live on:

https://xxxxxx.us-east-1.awsapprunner.com

5.3 Deploy Frontend to App Runner

Repeat the steps:

Use infra/Dockerfile.frontend

Expose port 8501

Environment variable:

API_URL=https://xxxxxx.us-east-1.awsapprunner.com/api/v1

5.4 WSS Support for Streamlit

App Runner supports WSS automatically.
Ensure your browser points to:

wss://xxxxx.awsapprunner.com/_stcore/stream

6. Deploying to AWS ECS Fargate

Use Fargate for long-term production.

6.1 Create ECR repos
aws ecr create-repository --repository-name recruiting-backend
aws ecr create-repository --repository-name recruiting-frontend


Push images same as before.

6.2 Create ECS Cluster

Fargate type

Public subnets

Attach IAM role for ECR pull & logs

6.3 Create two services:
Backend service

Container port: 8000

Load balancer target group: HTTP 80 → 8000

Environment variables via ECS task definition

Frontend service

Container port: 8501

Load balancer target group: HTTP/HTTPS 443 → 8501

Make sure target group supports WebSocket for Streamlit

6.4 ALB Listener Rules

Listener 443 → frontend TG (port 8501)

Listener 443 → backend TG (if you want api.mycompany.com)

Listener 80 → redirect to 443

Important:

AWS LB requires:

idle_timeout.timeout_seconds = 300


so Streamlit WebSockets don’t drop.

7. Deploying to Kubernetes (EKS/GKE/AKS)
7.1 Create Deployments

Example:

kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml


Each deployment:

Uses container image tag

Exposes service (ClusterIP)

7.2 Expose via Ingress

If using AWS ALB Ingress:

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: recruiting-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: app.mycompany.com
    http:
      paths:
      - path: /
        backend:
          service:
            name: frontend-svc
            port: 8501
  - host: api.mycompany.com
    http:
      paths:
      - path: /
        backend:
          service:
            name: backend-svc
            port: 8000

7.3 Secrets via Kubernetes

Store environment variables:

kubectl create secret generic recruiting-secrets \
  --from-env-file=.env


Mount into deployments.

8. Database (Production)

SQLite is fine for local development, not production.

Use:

PostgreSQL recommended providers:

AWS RDS

Supabase

Neon

Render.com

Aiven

Update your .env:

SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME

Run DB migrations?

The current system auto-creates schema at runtime (simple), but for production:

Install Alembic

Generate migrations (alembic revision)

Apply migrations (alembic upgrade head)

9. SSL / HTTPS

Depending on deployment method:

Docker Compose + Nginx:

Use Certbot:

sudo certbot --nginx -d app.mycompany.com -d api.mycompany.com

App Runner:

Handled automatically by AWS.

ECS:

Managed by ALB via ACM:

aws acm request-certificate --domain-name app.mycompany.com


Attach cert to ALB listener on port 443.

Kubernetes:

Use AWS Load Balancer Controller OR Cert-manager.

10. Scaling & Autoscaling
Backend scaling:

Stateless → safe to run N replicas

CPU-bound if embeddings or LLM calls

Add caching layer (Redis) for embeddings

Frontend scaling:

Streamlit is:

CPU-light

WebSocket-heavy (idle sessions)
Increase replicas:

replicas: 3

Database scaling:

Use RDS with:

Multi-AZ failover

Automated backups

Read replicas (optional)

11. Logging & Monitoring
AWS:

ECS → CloudWatch Logs

App Runner → CloudWatch Logs

RDS → Performance Insights

Use CloudWatch Metrics + Alarms

Kubernetes:

Use Prometheus + Grafana

Use ELK stack (ElasticSearch + Kibana)

Application-level logging:

Add Python logging handlers to:

Log every agent request

Log matching scores

Log job/candidate creation

12. Backups & Disaster Recovery
If using RDS:

Enable automated backups

Enable snapshot retention

Enable Multi-AZ

If using Serverless Postgres (Neon/Supabase):

Ensure nightly backups

Use PITR (point-in-time recovery)

File uploads:

Currently processed in-memory.
If storing long-term → use S3 bucket with lifecycle rules.

13. Production Hardening Checklist

 Use Postgres, not SQLite

 Enforce HTTPS everywhere

 Store secrets in SSM / AWS Secrets Manager

 Rotate JWT secret regularly

 Enable rate limiting (via Nginx or API gateway)

 Enable CORS restrictions in .env

 Enable CloudWatch alarms

 Put ALB idle timeout to 300s for Streamlit

 Add Alembic migrations

 Use container health checks

 Add CI/CD pipeline (GitHub → ECR → ECS/AppRunner)

14. Recommended Production Architecture (AWS)
                     ┌───────────────────────────────┐
                     │        Route 53 Domains        │
                     └──────────────┬────────────────┘
                                    │
                            ┌───────▼────────┐
                            │ ALB (HTTPS/WSS) │
                            └───┬─────────────┘
     ┌──────────────────────────┼───────────────────────────┐
     │                          │                           │
┌────▼─────┐              ┌─────▼─────┐              ┌──────▼─────┐
│Frontend  │              │Backend     │              │RDS Postgres │
│Streamlit │              │FastAPI     │              │Database     │
└────┬─────┘              └──────┬─────┘              └──────┬─────┘
     │                           │                            │
     └───────────────REST────────┴───────────────┐            │
                                                  │            │
                                            ┌─────▼─────┐     │
                                            │ OpenAI API │◄────┘
                                            └────────────┘

15. Final Notes

This deployment guide supports:

✔ Local dev
✔ Staging environment
✔ Full production deployment
✔ Serverless/Managed options
✔ Enterprise-grade architecture

If you need, I can also generate:

k8s/ manifests (Ingress, Services, Deployments)

ECS task definitions

GitHub Actions CI/CD pipelines (backend & frontend → ECR → ECS/AppRunner)

Terraform modules for the entire infrastructure

Helm chart for full deployment