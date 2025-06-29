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
