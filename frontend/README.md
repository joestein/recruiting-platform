# recruiting platform

```
cd recruiting-platform
cp .env.example backend/.env  # if you want
docker compose -f infra/docker-compose.yml up --build
```

Then hit:

Backend: http://localhost:8000/docs

Frontend: http://localhost:8501