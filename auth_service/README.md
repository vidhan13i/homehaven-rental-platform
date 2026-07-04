# Auth Service

## API Documentation (OpenAPI 3.0)

This service provides comprehensive REST API documentation automatically generated using `drf-spectacular`.

### How to Access
Once the docker containers are running, you can access the documentation via:
- **Swagger UI**: [http://localhost:8001/api/docs/](http://localhost:8001/api/docs/)
- **ReDoc**: [http://localhost:8001/api/redoc/](http://localhost:8001/api/redoc/)
- **Raw OpenAPI Schema**: [http://localhost:8001/api/schema/](http://localhost:8001/api/schema/)

### How to Generate Schema File
To export the schema as a YAML file for external clients or Postman:
```bash
docker compose exec auth_service python manage.py spectacular --file schema.yml
```

### Example Swagger UI
![Swagger UI Placeholder](/absolute/path/to/swagger_placeholder.png)
