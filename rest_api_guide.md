# REST API Best Practices Guide

## 1. Introduction

### What is a REST API?

REST (Representational State Transfer) is an architectural style for designing web APIs that use HTTP requests to access and manipulate data. A RESTful API treats server-side resources (like users, products, or orders) as entities that can be created, read, updated, and deleted using standard HTTP methods.

### Why Best Practices Matter

Following REST API best practices ensures:
- **Scalability**: Your API can handle growing traffic and data loads
- **Maintainability**: Code remains clean and easy to modify over time
- **Security**: Proper protection against common vulnerabilities
- **Developer Experience**: Other developers can easily understand and integrate with your API
- **Consistency**: Predictable behavior across all endpoints

## 2. Resource Design

### Use Nouns in URL Paths

Design your URLs around resources (nouns), not actions (verbs). Resources should represent the entities in your system.

**Good:**
```
GET /users
GET /products
GET /orders
```

**Bad:**
```
GET /getUsers
GET /fetchProducts
GET /retrieveOrders
```

### Proper Use of HTTP Verbs

Map HTTP methods to CRUD operations consistently:

- **GET**: Retrieve data (should be idempotent and safe)
- **POST**: Create new resources
- **PUT**: Update entire resource (idempotent)
- **PATCH**: Partial update of resource
- **DELETE**: Remove resource (idempotent)

```http
GET /users/123          # Get user with ID 123
POST /users             # Create new user
PUT /users/123          # Update entire user record
PATCH /users/123        # Update specific user fields
DELETE /users/123       # Delete user
```

### Nesting and Relationships

For related resources, use nested URLs but keep them shallow (max 2-3 levels):

```http
GET /users/123/orders           # Get orders for user 123
GET /users/123/orders/456       # Get specific order for user
POST /users/123/orders          # Create order for user
```

For complex relationships, consider using query parameters instead:
```http
GET /orders?user_id=123&status=pending
```

## 3. Versioning

### URL Path Versioning

The most common and explicit approach:

```http
GET /api/v1/users
GET /api/v2/users
```

### Header Versioning

More flexible but less visible:

```http
GET /api/users
Accept: application/vnd.api+json;version=1
```

### Introducing Changes Without Breaking Clients

- **Additive changes**: New fields, new endpoints (safe for existing clients)
- **Non-breaking changes**: Optional parameters, expanded responses
- **Breaking changes**: Require new version
  - Removing fields
  - Changing field types
  - Changing endpoint behavior

**Example of safe evolution:**
```json
// v1 response
{
  "id": 123,
  "name": "John Doe"
}

// v2 response (backwards compatible)
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com"  // New field added
}
```

## 4. HTTP Status Codes

Use standard HTTP status codes consistently:

### Success Codes (2xx)
- **200 OK**: Standard success response
- **201 Created**: Resource successfully created
- **204 No Content**: Success with no response body (often for DELETE)

### Client Error Codes (4xx)
- **400 Bad Request**: Invalid request syntax or parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied (authenticated but not authorized)
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource conflict (e.g., duplicate email)
- **422 Unprocessable Entity**: Valid syntax but semantic errors

### Server Error Codes (5xx)
- **500 Internal Server Error**: Generic server error
- **502 Bad Gateway**: Invalid response from upstream server
- **503 Service Unavailable**: Server temporarily unavailable

## 5. Request and Response Standards

### Consistent JSON Formatting

Always use JSON for modern APIs and maintain consistent structure:

```json
{
  "data": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "meta": {
    "timestamp": "2025-06-29T10:30:00Z",
    "version": "1.0"
  }
}
```

### Field Naming Conventions

Choose one convention and stick to it:

**snake_case (recommended for REST APIs):**
```json
{
  "user_id": 123,
  "first_name": "John",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**camelCase (common in JavaScript ecosystems):**
```json
{
  "userId": 123,
  "firstName": "John",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

### Using Proper Headers

Essential headers for REST APIs:

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Request-ID: unique-request-identifier
```

## 6. Authentication & Authorization

### Token-Based Authentication

**JWT (JSON Web Tokens):**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Benefits:
- Stateless (no server-side session storage)
- Contains user information
- Can include expiration and permissions

**OAuth2:**
More complex but industry standard for third-party integrations:
```http
Authorization: Bearer access_token_here
```

### Securing Endpoints

```javascript
// Example middleware for JWT validation
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }
  
  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
};
```

### Role-Based Access Control

```json
{
  "user_id": 123,
  "roles": ["user", "admin"],
  "permissions": ["read:users", "write:users"]
}
```

## 7. Filtering, Sorting, and Pagination

### Query Parameters Structure

Use clear, consistent parameter names:

```http
GET /products?category=electronics&min_price=100&max_price=500
GET /users?sort=created_at:desc&page=2&per_page=20
GET /orders?status=pending,processing&created_after=2025-01-01
```

### Pagination Best Practices

**Offset-based pagination:**
```http
GET /users?page=2&per_page=20
```

Response:
```json
{
  "data": [...],
  "pagination": {
    "current_page": 2,
    "per_page": 20,
    "total_pages": 15,
    "total_count": 300,
    "has_next": true,
    "has_prev": true
  }
}
```

**Cursor-based pagination (better for large datasets):**
```http
GET /users?cursor=eyJpZCI6MTIzfQ&limit=20
```

### HATEOAS-Style Links

Include navigation links in responses:

```json
{
  "data": [...],
  "links": {
    "self": "/api/v1/users?page=2",
    "next": "/api/v1/users?page=3",
    "prev": "/api/v1/users?page=1",
    "first": "/api/v1/users?page=1",
    "last": "/api/v1/users?page=15"
  }
}
```

## 8. Error Handling

### Structured Error Responses

Maintain consistent error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request data is invalid",
    "details": [
      {
        "field": "email",
        "message": "Email format is invalid"
      },
      {
        "field": "age",
        "message": "Age must be between 18 and 120"
      }
    ],
    "request_id": "req_12345abcde"
  }
}
```

### Meaningful Error Messages

Provide actionable error messages:

```json
// Bad
{
  "error": "Invalid input"
}

// Good
{
  "error": {
    "code": "INVALID_EMAIL",
    "message": "The email address format is invalid. Please provide a valid email like user@example.com"
  }
}
```

### Error Code Categories

Organize error codes logically:

```javascript
const ERROR_CODES = {
  // Authentication & Authorization
  AUTH_REQUIRED: 'AUTHENTICATION_REQUIRED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
  
  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',
  INVALID_FORMAT: 'INVALID_FORMAT',
  
  // Business Logic
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  DUPLICATE_RESOURCE: 'DUPLICATE_RESOURCE',
  BUSINESS_RULE_VIOLATION: 'BUSINESS_RULE_VIOLATION'
};
```

## 9. Documentation

### Using OpenAPI (Swagger)

Create machine-readable API documentation:

```yaml
openapi: 3.0.0
info:
  title: User Management API
  version: 1.0.0
  description: API for managing user accounts

paths:
  /users:
    get:
      summary: List all users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
```

### Keeping Documentation in Sync

**Automated approaches:**
- Generate docs from code annotations
- Use tools like `swagger-jsdoc` for Node.js
- Implement API-first design with schema validation

**Testing documentation:**
```javascript
// Example using Jest and supertest
describe('GET /users', () => {
  it('should match OpenAPI specification', async () => {
    const response = await request(app)
      .get('/users')
      .expect(200);
    
    // Validate response against OpenAPI schema
    expect(response.body).toMatchSchema(userListSchema);
  });
});
```

## 10. Testing

### Unit Testing Endpoints

```javascript
// Example using Jest and Express
describe('User Controller', () => {
  beforeEach(() => {
    // Setup test database
  });

  test('GET /users should return user list', async () => {
    const response = await request(app)
      .get('/api/v1/users')
      .set('Authorization', `Bearer ${validToken}`)
      .expect(200);

    expect(response.body.data).toBeInstanceOf(Array);
    expect(response.body.pagination).toBeDefined();
  });

  test('POST /users should create new user', async () => {
    const userData = {
      name: 'John Doe',
      email: 'john@example.com'
    };

    const response = await request(app)
      .post('/api/v1/users')
      .send(userData)
      .expect(201);

    expect(response.body.data.email).toBe(userData.email);
  });
});
```

### Integration Testing with Postman/Newman

Create comprehensive test collections:

```json
{
  "name": "User API Tests",
  "tests": [
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/users",
        "body": {
          "name": "Test User",
          "email": "test@example.com"
        }
      },
      "tests": [
        "pm.test('Status is 201', () => pm.response.to.have.status(201));",
        "pm.test('User has ID', () => pm.expect(pm.response.json().data.id).to.exist);"
      ]
    }
  ]
}
```

## 11. Performance & Scalability

### Caching Strategies

**HTTP Caching Headers:**
```http
Cache-Control: public, max-age=3600
ETag: "abc123def456"
Last-Modified: Wed, 29 Jun 2025 10:30:00 GMT
```

**Application-level caching:**
```javascript
// Redis caching example
const getUser = async (userId) => {
  const cacheKey = `user:${userId}`;
  
  // Try cache first
  let user = await redis.get(cacheKey);
  if (user) {
    return JSON.parse(user);
  }
  
  // Fetch from database
  user = await db.users.findById(userId);
  
  // Cache for 1 hour
  await redis.setex(cacheKey, 3600, JSON.stringify(user));
  
  return user;
};
```

### Rate Limiting and Throttling

```javascript
// Express rate limiting middleware
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    error: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Too many requests from this IP'
    }
  }
});

app.use('/api/', limiter);
```

### Connection Pooling

```javascript
// Database connection pooling
const pool = new Pool({
  host: 'localhost',
  database: 'myapi',
  user: 'dbuser',
  password: 'dbpass',
  max: 20, // maximum number of connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});
```

## 12. Final Tips

### Avoid Over-Engineering

Start simple and add complexity only when needed:

```javascript
// Simple is better
GET /users/123

// Don't over-complicate
GET /api/v1/domain/users/entities/123/profile/detailed
```

### Prioritize Consistency

**Consistent naming:**
```javascript
// Good - consistent pattern
GET /users
POST /users
GET /products  
POST /products

// Bad - inconsistent
GET /users
POST /user
GET /products
POST /create-product
```

### Design APIs with Consumers in Mind

**Provide what clients actually need:**
```json
// Instead of just user data
{
  "id": 123,
  "name": "John Doe"
}

// Include related data clients often need
{
  "id": 123,
  "name": "John Doe",
  "profile_image_url": "https://...",
  "last_login": "2025-06-29T10:30:00Z",
  "subscription": {
    "plan": "premium",
    "expires_at": "2025-12-31T23:59:59Z"
  }
}
```

**Allow clients to specify what they want:**
```http
# GraphQL-style field selection
GET /users/123?fields=id,name,email

# Include related resources
GET /users/123?include=orders,profile
```

---

## Quick Checklist

When building REST APIs, ensure you:

- ✅ Use nouns for resources and appropriate HTTP verbs
- ✅ Implement consistent error handling with meaningful messages  
- ✅ Version your API from the start
- ✅ Use standard HTTP status codes correctly
- ✅ Implement proper authentication and authorization
- ✅ Add pagination for list endpoints
- ✅ Write comprehensive documentation
- ✅ Include automated tests
- ✅ Consider performance (caching, rate limiting)
- ✅ Keep it simple and consistent

Remember: the best API is one that other developers love to use. Focus on clarity, consistency, and developer experience above all else.