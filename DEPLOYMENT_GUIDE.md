# ACIN Deployment & Setup Guide

## Amazon Circular Intelligence Network
**AI-Powered Multi-Agent Returns & Sustainable Resale Platform**

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [AWS Infrastructure Deployment](#aws-infrastructure-deployment)
4. [Backend Deployment (ECS Fargate)](#backend-deployment)
5. [Frontend Deployment (Vercel)](#frontend-deployment)
6. [MCP Configuration](#mcp-configuration)
7. [Environment Variables](#environment-variables)
8. [Testing & Verification](#testing-and-verification)

---

## Prerequisites

### Required Tools
```bash
# Node.js 20+
node --version  # v20.x.x

# Python 3.12+
python --version  # 3.12.x

# AWS CLI v2
aws --version

# AWS CDK
npm install -g aws-cdk
cdk --version

# Docker
docker --version

# Vercel CLI (for frontend)
npm install -g vercel
```

### Required AWS Services
- Amazon Bedrock (Claude Sonnet access enabled)
- Amazon DynamoDB
- Amazon S3
- Amazon ECS Fargate
- Amazon Cognito
- Amazon SQS
- Amazon Rekognition
- Amazon EventBridge
- Amazon Location Service
- AWS CloudWatch

### Enable Bedrock Model Access
1. Go to AWS Console → Amazon Bedrock → Model access
2. Request access to `anthropic.claude-sonnet-4-6-20250514-v1:0`
3. Wait for approval (usually instant for on-demand)

---

## Local Development Setup

### 1. Clone and Bootstrap
```bash
cd ACIN
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
Create `backend/.env`:
```env
AWS_REGION=us-east-1
S3_BUCKET=acin-uploads-YOUR_ACCOUNT_ID
DYNAMODB_TABLE=ACIN_Main
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6-20250514-v1:0
HIVE_API_KEY=your_hive_key_here
COGNITO_USER_POOL_ID=your_pool_id
COGNITO_CLIENT_ID=your_client_id
```

### 4. Run Backend Locally
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
API_URL=http://localhost:8000/v1
```

### 6. Run Frontend Locally
```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

---

## AWS Infrastructure Deployment

### 1. Configure AWS Credentials
```bash
aws configure
# Enter your Access Key ID, Secret Access Key, region (us-east-1)
```

### 2. Bootstrap CDK
```bash
cd infrastructure
npm install
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

### 3. Deploy Infrastructure Stack
```bash
cdk deploy ACINStack --require-approval never
```

This creates:
- DynamoDB table `ACIN_Main` with 9 GSIs
- S3 bucket `acin-uploads-YOUR_ACCOUNT_ID`
- S3 bucket `acin-legal-hold-YOUR_ACCOUNT_ID` (fraud evidence)
- 7 SQS FIFO queues with DLQs
- ECS Cluster `acin-cluster`
- VPC with 2 AZs
- Fargate task definition with IAM policies

### 4. Verify Resources
```bash
# Check DynamoDB table
aws dynamodb describe-table --table-name ACIN_Main

# Check S3 bucket
aws s3 ls | grep acin

# Check SQS queues
aws sqs list-queues | grep acin
```

---

## Backend Deployment

### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name acin-backend --region us-east-1
```

### 2. Build & Push Docker Image
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t acin-backend -f docker/Dockerfile .

# Tag
docker tag acin-backend:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/acin-backend:latest

# Push
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/acin-backend:latest
```

### 3. Deploy to ECS
```bash
aws ecs update-service \
  --cluster acin-cluster \
  --service acin-backend \
  --force-new-deployment
```

### 4. Verify Health
```bash
# Get the ALB DNS name from ECS service
curl https://YOUR_ALB_DNS/health
# Expected: {"status": "ok", "service": "acin-backend", "version": "1.0.0"}
```

---

## Frontend Deployment

### 1. Deploy to Vercel
```bash
cd frontend
vercel deploy --prod
```

### 2. Configure Environment Variables in Vercel
In Vercel dashboard → Settings → Environment Variables:
```
NEXT_PUBLIC_API_URL=https://api.acin.amazonaws.com/v1
API_URL=https://api.acin.amazonaws.com/v1
```

### 3. Configure Custom Domain (Optional)
In Vercel dashboard → Domains → Add `acin.vercel.app`

---

## MCP Configuration

### For Kiro IDE Integration
Create `.kiro/settings/mcp.json` in workspace root:

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    },
    "dynamodb": {
      "command": "uvx",
      "args": ["awslabs.aws-dynamodb-mcp-server@latest"],
      "env": {
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["list_tables", "describe_table"]
    },
    "bedrock": {
      "command": "uvx",
      "args": ["awslabs.amazon-bedrock-mcp-server@latest"],
      "env": {
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### MCP Servers for Development

#### AWS Documentation MCP
Provides access to AWS service documentation for reference during development.
```bash
# Test: uvx should auto-download and run
uvx awslabs.aws-documentation-mcp-server@latest
```

#### DynamoDB MCP
Enables direct DynamoDB table inspection and querying from the IDE.

#### Bedrock MCP
Provides model invocation and testing capabilities.

### Required Environment for MCP
Ensure these are set in your shell or `.env`:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

---

## Environment Variables

### Backend (.env)
| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET` | Upload bucket name | `acin-uploads-123456789012` |
| `DYNAMODB_TABLE` | Main table name | `ACIN_Main` |
| `BEDROCK_MODEL_ID` | Claude model ID | `anthropic.claude-sonnet-4-6-20250514-v1:0` |
| `HIVE_API_KEY` | Hive AI API key (post-hackathon) | `your_key` |
| `COGNITO_USER_POOL_ID` | Cognito pool ID | `us-east-1_xxxxx` |
| `COGNITO_CLIENT_ID` | Cognito app client ID | `xxxxxxxxxx` |

### Frontend (.env.local)
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Public API base URL | `https://api.acin.amazonaws.com/v1` |
| `API_URL` | Server-side API URL | `https://api.acin.amazonaws.com/v1` |

### GitHub Secrets (CI/CD)
| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `VERCEL_TOKEN` | Vercel deployment token |

---

## Testing & Verification

### 1. API Health Check
```bash
curl http://localhost:8000/health
```

### 2. Submit Test Return
```bash
curl -X POST http://localhost:8000/v1/returns \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "B09XS7JWHH",
    "customer_id": "C-28374-MH",
    "return_reason": "defective",
    "image_urls": [
      "s3://acin-uploads/RET-42/front.jpg",
      "s3://acin-uploads/RET-42/back.jpg"
    ],
    "location": {
      "lat": 19.076,
      "lng": 72.877,
      "city": "Mumbai",
      "pincode": "400001"
    }
  }'
```

### 3. Check Decision
```bash
curl http://localhost:8000/v1/returns/RET-2025-08-0042/decision
```

### 4. Verify DynamoDB
```bash
aws dynamodb query \
  --table-name ACIN_Main \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk": {"S": "RETURN#RET-2025-08-0042"}}'
```

### 5. Check Impact Metrics
```bash
curl http://localhost:8000/v1/analytics/impact
```

---

## Architecture Summary

```
Customer (Next.js) → S3 Upload → FastAPI + Validation Gate (Step-0)
    → LangGraph Orchestrator → 5 Agents + Bedrock (parallel)
    → ACIN_Main (DynamoDB) → Decision Fusion Engine
    → FastAPI → Frontend (Decision + Explanation)
    → Impact Dashboard (DynamoDB Streams)
```

### Key Design Decisions
1. **NEVER use analysis_id as PK** — always `RETURN#<return_id>`
2. **Fraud signals kept separate**: `image_fcs` (authenticity) vs `fraud_probability` (condition-claim)
3. **Validation Gate runs BEFORE agents** — cost efficiency + security boundary
4. **Single query retrieves entire case**: `Query(PK=RETURN#id)`
5. **Immutable audit trail**: Every decision has CARBON_TXN and EVENT records

---

## Troubleshooting

### Bedrock Access Denied
```bash
# Verify model access
aws bedrock get-foundation-model --model-identifier anthropic.claude-sonnet-4-6-20250514-v1:0
```

### DynamoDB Table Not Found
```bash
# Redeploy CDK
cd infrastructure && cdk deploy ACINStack
```

### ECS Service Unhealthy
```bash
# Check logs
aws logs get-log-events --log-group-name /acin/backend --log-stream-name latest
```

---

## Quick Commands Reference

```bash
# Local dev
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Deploy all
cd infrastructure && cdk deploy ACINStack
docker build -t acin-backend -f docker/Dockerfile . && docker push ...
aws ecs update-service --cluster acin-cluster --service acin-backend --force-new-deployment
cd frontend && vercel deploy --prod

# Verify
curl https://api.acin.amazonaws.com/v1/health
```
