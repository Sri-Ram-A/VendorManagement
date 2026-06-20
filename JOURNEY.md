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
celery -A config worker -l info
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