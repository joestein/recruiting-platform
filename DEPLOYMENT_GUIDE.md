# Deployment Guide – Recruiting SaaS Platform

How to deploy the platform across local production-like runs, single VMs, and managed cloud targets. Includes env vars, SSL, WSS, scaling, logging, and DR notes.

## 1) Deployment Architecture
- Backend (FastAPI): port 8000; behind reverse proxy/LB; needs Python deps, `.env`, persistent DB (SQLite dev; Postgres prod).
- Frontend (Streamlit): port 8501; talks to backend via REST; requires WSS support.
- Database: SQLite for dev; Postgres recommended (RDS/Supabase/Neon/Render).

## 2) Environment Variables
Copy `.env.example` → `.env`:
```
SECRET_KEY=CHANGE_ME
SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db
# Prod Postgres:
# SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME
BACKEND_CORS_ORIGINS=http://localhost:8501
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
MATCHING_USE_OPENAI=false
```
Inject in prod via SSM Parameter Store, Docker Compose `.env`, ECS task env, K8s Secrets, or App Runner encrypted env.

## 3) Local Production Simulation (Docker Compose)
- Run: `docker-compose -f infra/docker-compose.yml up --build`
- Services:
  - FastAPI backend: http://localhost:8000
  - Docs: http://localhost:8000/docs
  - Streamlit frontend: http://localhost:8501
- Stop: `docker-compose down`; detached: `docker-compose up -d`.

## 4) Single VM (Ubuntu/EC2/DigitalOcean)
1. Install: `sudo apt update && sudo apt install -y docker.io docker-compose` and `sudo systemctl enable docker --now`.
2. Clone repo: `git clone https://github.com/your-org/recruiting-platform.git && cd recruiting-platform`.
3. Configure `.env` (use Postgres recommended): `SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/db`.
4. Run: `docker-compose -f infra/docker-compose.yml up -d --build`.
5. Add reverse proxy + SSL (Nginx/Caddy). Nginx example for frontend domain:
```
server {
    listen 80;
    server_name app.mycompany.com;
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
   - Certbot: `sudo certbot --nginx -d app.mycompany.com`.
   - Streamlit needs WSS over 443; keep upgrade headers.

## 5) AWS App Runner (Easiest Managed)
1. Backend image (use `infra/Dockerfile.backend`):
   - `aws ecr create-repository --repository-name recruiting-backend`
   - `docker build -t recruiting-backend -f infra/Dockerfile.backend .`
   - `docker tag recruiting-backend:latest <ECR_URL>/recruiting-backend:latest`
   - `docker push <ECR_URL>/recruiting-backend:latest`
2. Deploy backend:
   - App Runner from ECR, port 8000, set env vars (.env contents).
   - Result: `https://xxxxxx.us-east-1.awsapprunner.com`.
3. Frontend image (`infra/Dockerfile.frontend`), port 8501; env `API_URL=https://xxxxxx.us-east-1.awsapprunner.com/api/v1`.
4. WSS: App Runner supports WSS; browser uses `wss://.../_stcore/stream`.

## 6) AWS ECS Fargate
1. Create ECR repos (`recruiting-backend`, `recruiting-frontend`) and push images as above.
2. Create ECS Fargate cluster (public subnets, IAM for ECR/logs).
3. Services:
   - Backend: container port 8000; ALB target group HTTP 80 → 8000; env via task def.
   - Frontend: container port 8501; ALB target group HTTPS 443 → 8501; target group supports WebSocket.
4. ALB listeners:
   - 443 → frontend TG (app.mycompany.com)
   - 443 → backend TG (api.mycompany.com) if split domains
   - 80 → redirect to 443
5. Set ALB idle timeout to 300s to avoid Streamlit websocket drops.

## 7) Kubernetes (EKS/GKE/AKS)
1. Apply deployments/services (examples in `k8s/`):
   - `kubectl apply -f k8s/backend-deployment.yaml`
   - `kubectl apply -f k8s/frontend-deployment.yaml`
2. Ingress (AWS ALB example):
```yaml
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
        pathType: Prefix
        backend:
          service:
            name: frontend-svc
            port:
              number: 8501
  - host: api.mycompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-svc
            port:
              number: 8000
```
3. Secrets: `kubectl create secret generic recruiting-secrets --from-env-file=.env` and mount in deployments.

## 8) Database (Production)
- Use Postgres (RDS, Supabase, Neon, Render, Aiven).
- `.env`: `SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME`.
- Migrations: current app auto-creates schema; for prod, add Alembic (`alembic revision`, `alembic upgrade head`).

## 9) SSL / HTTPS
- Docker Compose + Nginx: Certbot `sudo certbot --nginx -d app.mycompany.com -d api.mycompany.com`.
- App Runner: handled automatically.
- ECS: use ACM cert on ALB 443 listener (`aws acm request-certificate --domain-name app.mycompany.com`).
- K8s: AWS Load Balancer Controller or cert-manager for TLS.

## 10) Scaling & Autoscaling
- Backend: stateless; scale replicas; CPU-heavy when using embeddings/LLM; consider Redis cache for embeddings.
- Frontend: CPU-light, websocket-heavy; start with `replicas: 3`.
- DB: RDS Multi-AZ, automated backups, optional read replicas.

## 11) Logging & Monitoring
- AWS: ECS/App Runner → CloudWatch Logs; RDS Performance Insights; metrics/alarms in CloudWatch.
- K8s: Prometheus + Grafana; ELK (ElasticSearch + Kibana).
- App logging: add Python handlers to log agent requests, matching scores, job/candidate creation.

## 12) Backups & DR
- RDS: automated backups, snapshot retention, Multi-AZ.
- Serverless Postgres (Neon/Supabase): nightly backups, PITR.
- File uploads: currently in-memory; if storing, use S3 with lifecycle rules.

## 13) Production Hardening Checklist
- Use Postgres (not SQLite).
- Enforce HTTPS everywhere.
- Store secrets in SSM / Secrets Manager.
- Rotate JWT secret regularly.
- Enable rate limiting (Nginx/API gateway).
- Restrict CORS in `.env`.
- CloudWatch (or equivalent) alarms.
- ALB idle timeout 300s for Streamlit.
- Add Alembic migrations.
- Use container health checks.
- Add CI/CD pipeline (GitHub → ECR → ECS/App Runner).

## 14) Recommended AWS Architecture
```
Route53
  │
ALB (HTTPS/WSS)
  ├── Frontend (Streamlit, 8501)
  ├── Backend (FastAPI, 8000)
  └── RDS Postgres
      └── OpenAI API
```

## 15) Extras
Available on request: K8s manifests (Ingress/Services/Deployments), ECS task definitions, GitHub Actions CI/CD (backend/frontend → ECR → ECS/App Runner), Terraform modules, Helm chart.
