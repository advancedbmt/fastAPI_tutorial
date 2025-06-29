# FastAPI Docker Tutorial with Swagger Documentation

This tutorial will guide you through creating a FastAPI application, containerizing it with Docker, and exploring the automatic Swagger documentation.

## Project Structure

```
fastapi-docker-app/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── models.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Step 1: Create the FastAPI Application

### `requirements.txt`

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.4.2
```

### `app/__init__.py`

```python
# Empty file to make app a Python package
```

### `app/models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    age: int = Field(..., ge=0, le=150, description="User's age")

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    is_active: bool = Field(default=True, description="Whether the user is active")

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    is_active: Optional[bool] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
```

### `app/main.py`

```python
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict
from datetime import datetime
import uvicorn

from .models import User, UserCreate, UserUpdate, HealthCheck

# Create FastAPI app with custom metadata for Swagger
app = FastAPI(
    title="User Management API",
    description="""
    A simple User Management API built with FastAPI.
    
    ## Features
    
    * **Create users** - Add new users to the system
    * **Read users** - Get user information by ID or list all users
    * **Update users** - Modify existing user information
    * **Delete users** - Remove users from the system
    * **Health check** - Monitor API status
    
    This API demonstrates FastAPI capabilities including:
    - Automatic OpenAPI (Swagger) documentation
    - Request/response validation with Pydantic
    - Type hints and data validation
    - Error handling and HTTP status codes
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# In-memory database simulation
users_db: Dict[int, User] = {}
next_user_id = 1

@app.get("/", 
         summary="Root endpoint",
         description="Welcome message for the API")
async def root():
    """Returns a welcome message."""
    return {"message": "Welcome to the User Management API! Visit /docs for Swagger documentation."}

@app.get("/health", 
         response_model=HealthCheck,
         summary="Health check",
         description="Check if the API is running properly")
async def health_check():
    """
    Perform a health check on the API.
    
    Returns:
        HealthCheck: Current status, timestamp, and version information
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@app.post("/users/", 
          response_model=User, 
          status_code=status.HTTP_201_CREATED,
          summary="Create a new user",
          description="Create a new user with the provided information")
async def create_user(user: UserCreate):
    """
    Create a new user.
    
    Args:
        user: User information including name, email, and age
        
    Returns:
        User: The created user with assigned ID and creation timestamp
    """
    global next_user_id
    
    # Check if email already exists
    for existing_user in users_db.values():
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    new_user = User(
        id=next_user_id,
        name=user.name,
        email=user.email,
        age=user.age,
        created_at=datetime.now(),
        is_active=True
    )
    
    users_db[next_user_id] = new_user
    next_user_id += 1
    
    return new_user

@app.get("/users/", 
         response_model=List[User],
         summary="Get all users",
         description="Retrieve a list of all users in the system")
async def get_users(skip: int = 0, limit: int = 100):
    """
    Retrieve all users with optional pagination.
    
    Args:
        skip: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        
    Returns:
        List[User]: List of users
    """
    users_list = list(users_db.values())
    return users_list[skip: skip + limit]

@app.get("/users/{user_id}", 
         response_model=User,
         summary="Get user by ID",
         description="Retrieve a specific user by their ID")
async def get_user(user_id: int):
    """
    Retrieve a specific user by ID.
    
    Args:
        user_id: The ID of the user to retrieve
        
    Returns:
        User: The requested user information
        
    Raises:
        HTTPException: If user is not found
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return users_db[user_id]

@app.put("/users/{user_id}", 
         response_model=User,
         summary="Update user",
         description="Update an existing user's information")
async def update_user(user_id: int, user_update: UserUpdate):
    """
    Update an existing user's information.
    
    Args:
        user_id: The ID of the user to update
        user_update: The fields to update (only non-null fields will be updated)
        
    Returns:
        User: The updated user information
        
    Raises:
        HTTPException: If user is not found or email already exists
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    current_user = users_db[user_id]
    update_data = user_update.dict(exclude_unset=True)
    
    # Check email uniqueness if email is being updated
    if "email" in update_data:
        for uid, existing_user in users_db.items():
            if uid != user_id and existing_user.email == update_data["email"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
    
    # Update user fields
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    return current_user

@app.delete("/users/{user_id}",
           status_code=status.HTTP_204_NO_CONTENT,
           summary="Delete user",
           description="Delete a user from the system")
async def delete_user(user_id: int):
    """
    Delete a user from the system.
    
    Args:
        user_id: The ID of the user to delete
        
    Raises:
        HTTPException: If user is not found
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    del users_db[user_id]
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content={"message": "User deleted successfully"}
    )

# Custom exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Step 2: Create the Dockerfile

### `Dockerfile`

```dockerfile
# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Step 3: Create Docker Compose (Optional)

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  fastapi-app:
    build: .
    container_name: fastapi-user-api
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./app:/app/app  # For development hot-reload
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add a reverse proxy
  nginx:
    image: nginx:alpine
    container_name: fastapi-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - fastapi-app
    restart: unless-stopped
```

## Step 4: Build and Run

### Option 1: Using Docker directly

```bash
# Build the image
docker build -t fastapi-user-api .

# Run the container
docker run -d --name fastapi-app -p 8000:8000 fastapi-user-api

# View logs
docker logs fastapi-app

# Stop and remove
docker stop fastapi-app
docker rm fastapi-app
```

### Option 2: Using Docker Compose

```bash
# Build and start services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Step 5: Access Swagger Documentation

Once your container is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **API Root**: http://localhost:8000/

## Step 6: Test the API

### Using curl:

```bash
# Health check
curl http://localhost:8000/health

# Create a user
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "email": "john@example.com", "age": 30}'

# Get all users
curl http://localhost:8000/users/

# Get specific user
curl http://localhost:8000/users/1

# Update user
curl -X PUT "http://localhost:8000/users/1" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Smith", "age": 31}'

# Delete user
curl -X DELETE http://localhost:8000/users/1
```

### Using the Swagger UI:

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out" button
4. Fill in the required parameters
5. Click "Execute" to test the API

## Key Features Demonstrated

### FastAPI Features:
- **Automatic API documentation** with Swagger UI and ReDoc
- **Request/response validation** using Pydantic models
- **Type hints** for better code quality and IDE support
- **Dependency injection** capabilities
- **Exception handling** with custom error responses
- **HTTP status codes** for proper REST API responses

### Docker Best Practices:
- **Multi-stage builds** for optimized image size
- **Non-root user** for security
- **Health checks** for container monitoring
- **Environment variables** for configuration
- **Volume mounting** for development

### Swagger Documentation Features:
- **Interactive API testing** directly from the browser
- **Detailed endpoint descriptions** with examples
- **Request/response schemas** automatically generated
- **Parameter validation** with constraints
- **Error response documentation**

## Production Considerations

For production deployment, consider:

1. **Environment Variables**: Use environment variables for configuration
2. **Database**: Replace in-memory storage with a real database
3. **Authentication**: Add JWT or OAuth2 authentication
4. **Rate Limiting**: Implement rate limiting for API protection
5. **Logging**: Add structured logging
6. **Monitoring**: Add metrics and monitoring
7. **HTTPS**: Use SSL/TLS certificates
8. **Load Balancing**: Use multiple container instances

This tutorial provides a solid foundation for building and containerizing FastAPI applications with comprehensive Swagger documentation.