# Docling setup
- If you get file not found error while running (put yout file path)  
mkdir -p /home/srirama/micromamba/envs/pytorch/lib/python3.12/site-packages/rapidocr/models

# Celery and Redis
```bash
## https://hub.docker.com/_/redis
podman run -d \
  --name redis-cc \
  -p 6379:6379 \
  -v redis_data:/data \
  redis
celery -A backend worker -l info
```

# Docker
```bash
micromamba install neo4j-python-driver -c conda-forge -y
mkdir -p ~/neo4j/data
podman run -d \
    --name neo4j-sg
    --publish=7474:7474 --publish=7687:7687 \
    --volume=$HOME/neo4j/data:/data \
    neo4j
```
`Ctrl+Shift+P` Run:Tasks -> Run all tasks
# Because fo chromadb
TypeError: Descriptors cannot be created directly.
If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
If you cannot immediately regenerate your protos, some other possible workarounds are:
 1. Downgrade the protobuf package to 3.20.x or lower.
 2. Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python (but this will use pure-Python parsing and will be much slower).
 pip install -U \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-proto \
    opentelemetry-exporter-otlp-proto-grpc

python manage.py spectacular --file schema.yaml
npm install -D openapi-typescript
npm install openapi-fetch
npx openapi-typescript /home/srirama/Documents/sr_proj/VendorManagement/backend/schema.yaml -o ./types/schema.ts

24097cd2-e08c-4f04-97ad-497ae74c686d

micromamba activate pytorch
cd backend
python manage.py runserver
podman start redis-cc
celery -A backend worker -l info