# Profile Service

## API Documentation (OpenAPI 3.0)

This service provides comprehensive REST API documentation automatically generated using `drf-spectacular`.

### How to Access
Once the docker containers are running, you can access the documentation via:
- **Swagger UI**: [http://localhost:8002/api/docs/](http://localhost:8002/api/docs/)
- **ReDoc**: [http://localhost:8002/api/redoc/](http://localhost:8002/api/redoc/)
- **Raw OpenAPI Schema**: [http://localhost:8002/api/schema/](http://localhost:8002/api/schema/)

### How to Generate Schema File
To export the schema as a YAML file for external clients or Postman:
```bash
docker compose exec profile_service python manage.py spectacular --file schema.yml
```

### Example Swagger UI
![Swagger UI Placeholder](/absolute/path/to/swagger_placeholder.png)
