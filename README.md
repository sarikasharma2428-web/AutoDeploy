## AutoDeployX

AI-assisted repository analysis with FastAPI, Vite/React, Qdrant-powered RAG, Prometheus/Grafana monitoring, Terraform infrastructure, and GitHub Actions CI/CD.

```
                         +-------------------+
                         |   Frontend (Vite) |
                         +---------+---------+
                                   |
                                   v
                   +---------------+---------------+
                   |        Backend (FastAPI)      |
                   |  - repo cloning & parsing     |
                   |  - embeddings & Qdrant RAG    |
                   |  - LLM orchestration          |
                   +------+-----------+------------+
                          |           |
                          v           v
                +---------+--+   +----+----------------+
                | Qdrant DB |   | LLM providers        |
                | (Vectors) |   | (local/OpenAI/HF)    |
                +-----------+   +----------------------+
                          |
                          v
         +----------------+--------------+
         | Prometheus + Grafana (metrics)|
         +-------------------------------+
```

### Highlights

- Deterministic `/api/repo/analyze` endpoint that clones, chunks, embeds, stores in Qdrant, runs LLM analysis, and returns structured JSON with source citations.
- Backend health metrics exposed at `/metrics`, collected by Prometheus, visualized via Grafana dashboard provisioning.
- Animated landing page with CTA modal plus analyzer view featuring live progress UI, security table, code sample viewer, and DevOps checklist.
- Docker Compose stack with backend, frontend, Qdrant, Prometheus, and Grafana (ports 8000/3000/6333/9090/3001).
- Kubernetes manifests (namespace, config map, secrets template, Deployments, qdrant StatefulSet w/ PVC note, ingress, deploy script) ready for `kubectl` apply.
- Terraform modules for VPC, IAM, EC2 (t2.micro), ECR, and S3 with billing callouts in `terraform/README.md`.
- GitHub Actions workflow building/pushing Docker images to ECR and rolling deployments via kubectl.

---

## Environment variables

Copy `.env.example` to `.env` and fill in secrets:

| Variable | Description |
| --- | --- |
| `LOCAL_LLM_PATH` | Absolute path to local `*.gguf` file if running llama.cpp locally |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Optional hosted fallback (e.g. `gpt-4o-mini`) |
| `HUGGINGFACE_API_KEY` / `HUGGINGFACE_MODEL` | Second fallback for hosted inference |
| `QDRANT_HOST` / `QDRANT_PORT` | Default `qdrant:6333` inside Docker/K8s |
| `PROMETHEUS_METRICS_PATH` | Typically `/metrics` |
| `REACT_APP_API_URL` / `VITE_API_URL` | Frontend API base (Compose & k8s set automatically) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | Required for Terraform + CI push |
| `ECR_REGISTRY`, `ECR_BACKEND_REPO`, `ECR_FRONTEND_REPO`, `PUBLIC_API_URL`, `KUBE_CONFIG` (base64) | GitHub Actions secrets |

Never commit `.env`. Use `LOCAL_LLM_PATH` for llama.cpp, or set hosted keys for OpenAI/HuggingFace.

---

## Local development

### Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

### Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # production build
```

### Running tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                            # unit tests
RUN_INTEGRATION_TESTS=1 pytest    # runs live repo smoke test (requires Qdrant + models)
```

---

## Docker Compose

```bash
# Build and start everything (backend, frontend, qdrant, prometheus, grafana)
docker-compose up --build

# Access:
#   Backend API docs:   http://localhost:8000/api/docs
#   Frontend UI:        http://localhost:3000
#   Qdrant console:     http://localhost:6333
#   Prometheus:         http://localhost:9090
#   Grafana:            http://localhost:3001 (admin/admin by default)
```

Services include health checks and `restart: unless-stopped`. Update `.env` for credentials or overrides.

---

## Kubernetes

Files under `k8s/` provide namespace, config, secrets template, Deployments, qdrant StatefulSet (with PVC template), ingress, and `deploy.sh`.

```bash
# edit k8s/secret-template.yaml with real keys, then:
kubectl apply -f k8s/secret-template.yaml

# deploy (set BACKEND_IMAGE / FRONTEND_IMAGE envs as needed)
NAMESPACE=autodeployx BACKEND_IMAGE=ghcr.io/you/backend:TAG FRONTEND_IMAGE=ghcr.io/you/frontend:TAG ./k8s/deploy.sh
```

`k8s/deploy.sh` patches image tags and waits for rollouts. Adjust ingress host `autodeployx.local` as required.

---

## Terraform (AWS)

`terraform/` provisions:

- VPC with public subnet + routing
- IAM instance profile
- Single `t2.micro` EC2 VM (Docker Compose host)
- S3 bucket for artifacts/logs
- ECR repositories for backend & frontend

Usage:

```bash
cd terraform
terraform init
terraform apply -var-file="environments/dev/terraform.tfvars"
```

See `terraform/README.md` for billing notes (Elastic IP, ECR storage, S3 usage).

---

## CI/CD

`.github/workflows/ci.yml` runs on pushes/PRs:

1. Python + Node tests (`pytest`, `npm run build`)
2. Docker build & push to ECR (`ECR_REGISTRY`, `ECR_BACKEND_REPO`, `ECR_FRONTEND_REPO`)
3. `kubectl set image` rollout using `KUBE_CONFIG` secret (base64 kubeconfig)

Set secrets in repository settings:

- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- `ECR_REGISTRY`, `ECR_BACKEND_REPO`, `ECR_FRONTEND_REPO`
- `PUBLIC_API_URL`
- `KUBE_CONFIG` (base64 encoded kubeconfig)

---

## Monitoring & dashboards

- Prometheus scrapes backend metrics from `/metrics` and stores rules from `monitoring/prometheus/alerts.yml`.
- Grafana auto-loads `monitoring/grafana/dashboards/application-dashboard.json` and Prometheus datasource provisioning.
- Alerts focus on HTTP error rate, latency, and service uptime; extend as needed for cluster metrics.

---

## LLM orchestration

`services/llm_engine.py` picks providers automatically:

1. `LOCAL_LLM_PATH` + `llama-cpp-python` (quantized gguf)
2. `OPENAI_API_KEY` / `OPENAI_MODEL`
3. `HUGGINGFACE_API_KEY` / `HUGGINGFACE_MODEL`
4. Deterministic heuristic fallback (still cites top references)

Temperature defaults to `0.0`, and output schema enforces JSON structure with `reference_id` fields so every claim links to `source_references`.

---

## Validation checklist

- [x] `/health` exposes status + version + dependency states.
- [x] `/api/repo/analyze` clones, reads, chunks, stores, queries Qdrant, runs LLM (or fallback), and returns structured JSON with citations.
- [x] Frontend analyzer shows progress, structured cards, security table, code snippets, improvement plan, CI/CD checklist.
- [x] Docker Compose runs backend, frontend, qdrant, Prometheus, Grafana with health checks and restarts.
- [x] Kubernetes manifests include namespace, configmap, secrets template, Deployments, qdrant StatefulSet + PVC guidance, ingress, deploy script.
- [x] Terraform provisions VPC, IAM, EC2 (t2.micro), ECR, S3 with documented billing risks.
- [x] Prometheus scrapes backend metrics; Grafana dashboard + datasources provisioned.
- [x] Tests include FastAPI unit tests + optional integration smoke test against a public repo.
- [x] GitHub Actions workflow builds/pushes images and deploys to Kubernetes.
