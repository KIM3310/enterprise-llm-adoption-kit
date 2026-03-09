# Enterprise LLM Adoption Kit GCP Terraform

Minimal Cloud Run deployment skeleton for the backend runtime in `enterprise-llm-adoption-kit`.

## Apply

```bash
terraform init
terraform apply \
  -var="project_id=your-project" \
  -var="image=asia-northeast3-docker.pkg.dev/your-project/apps/enterprise-llm-adoption-kit-api:latest"
```

Use `env` to inject auth, Azure/OpenAI settings, and runtime scorecard configuration.
