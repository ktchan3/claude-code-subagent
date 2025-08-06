# API Reference

This document provides comprehensive documentation for the People Management System REST API, including endpoints, authentication, request/response formats, and usage examples.

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Base URL and Versioning](#base-url-and-versioning)
- [Request/Response Format](#requestresponse-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [People Endpoints](#people-endpoints)
- [Departments Endpoints](#departments-endpoints)
- [Positions Endpoints](#positions-endpoints)
- [Employment Endpoints](#employment-endpoints)
- [Statistics Endpoints](#statistics-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Client SDK Usage](#client-sdk-usage)
- [Examples](#examples)

## API Overview

The People Management System API is a RESTful web service that provides comprehensive functionality for managing people, departments, positions, and employment records. The API follows REST principles and returns JSON-formatted responses.

### Key Features

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON API**: All requests and responses use JSON format
- **Pagination**: Built-in pagination for list endpoints
- **Filtering & Search**: Advanced filtering and search capabilities
- **Validation**: Comprehensive input validation using Pydantic
- **Error Handling**: Standardized error responses
- **Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Type Safety**: Full type annotations throughout

### API Characteristics

- **Stateless**: Each request contains all necessary information
- **Idempotent**: Safe operations can be repeated without side effects
- **Cacheable**: GET requests include appropriate cache headers
- **Uniform Interface**: Consistent URL patterns and response formats

## Authentication

The API supports optional API key authentication for enhanced security and rate limiting.

### API Key Authentication

Include the API key in the request header:

```http
Authorization: Bearer your-api-key-here
```

### Obtaining an API Key

API keys can be obtained through the admin interface or by contacting system administrators.

### Public Access

Many endpoints allow public access without authentication, but authenticated requests receive higher rate limits and access to additional features.

## Base URL and Versioning

### Base URL

```
Production: https://api.yourdomain.com
Development: http://localhost:8000
```

### API Versioning

The API uses URL path versioning:

```
/api/v1/...
```

Current version: **v1.0.0**

### Version History

| Version | Release Date | Status | Notes |
|---------|--------------|--------|-------|
| v1.0.0  | 2024-01-01  | Current | Initial release |

## Request/Response Format

### Content Type

All requests and responses use JSON format:

```http
Content-Type: application/json
```

### Standard Response Format

All successful responses follow this structure:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid-here"
  }
}
```

### Paginated Response Format

List endpoints return paginated results:

```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": {
    "items": [
      // Array of items
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8,
      "has_next": true,
      "has_prev": false,
      "next_page": 2,
      "prev_page": null
    }
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid-here"
  }
}
```

### Query Parameters

#### Pagination Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-based) |
| `per_page` | integer | 20 | Items per page (max: 100) |

#### Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search query across relevant fields |
| `sort_by` | string | Field to sort by |
| `sort_order` | string | Sort order: "asc" or "desc" |

#### Filter Parameters

Vary by endpoint, typically include:
- `created_after`: Filter by creation date
- `created_before`: Filter by creation date
- `is_active`: Filter by active status
- `department_id`: Filter by department

## Error Handling

### Error Response Format

All error responses follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error details
    }
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid-here"
  }
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| 200 | OK | Successful GET, PUT requests |
| 201 | Created | Successful POST requests |
| 204 | No Content | Successful DELETE requests |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Server temporarily unavailable |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `NOT_FOUND` | Requested resource not found |
| `ALREADY_EXISTS` | Resource already exists |
| `PERMISSION_DENIED` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVER_ERROR` | Internal server error |

### Validation Errors

Validation errors include field-specific details:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "email": ["Invalid email format"],
        "phone": ["Phone number is required"]
      }
    }
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage and system stability.

### Rate Limits

| User Type | Requests per Minute | Burst Limit |
|-----------|-------------------|-------------|
| Anonymous | 60 | 10 |
| Authenticated | 200 | 20 |
| Premium | 500 | 50 |

### Rate Limit Headers

Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 150
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

### Rate Limit Exceeded

When rate limit is exceeded, a 429 status code is returned:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again later.",
    "details": {
      "retry_after": 60,
      "limit": 200,
      "window": 60
    }
  }
}
```

## People Endpoints

Manage person records including personal information and employment history.

### Important API Usage Notes

#### Field Handling and Optional Parameters

**Critical**: When creating or updating person records, the API properly handles optional fields. You should only include fields that you want to set. Omitted optional fields will not override existing values.

**Correct Usage**:
```json
{
  "first_name": "John",
  "last_name": "Doe", 
  "email": "john.doe@example.com",
  "title": "Dr"
}
```

**Field Exclusion Behavior**:
- Optional fields that are not provided in the request will be ignored
- Optional fields explicitly set to `null` will be stored as `null`
- This prevents accidental data loss when updating partial records

#### Date Format

All date fields use DD-MM-YYYY format (e.g., "25-12-1990" for December 25, 1990).

#### Tags Field

The `tags` field accepts an array of strings for categorization:
```json
{
  "tags": ["engineering", "senior", "team-lead"]
}
```

### List People

```http
GET /api/v1/people
```

Retrieve a paginated list of people.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Items per page |
| `search` | string | Search in name, email |
| `sort_by` | string | Sort field: "first_name", "last_name", "email", "created_at" |
| `sort_order` | string | Sort order: "asc", "desc" |
| `department_id` | string | Filter by department |
| `is_employed` | boolean | Filter by employment status |
| `created_after` | string | Filter by creation date (ISO format) |

#### Response

```json
{
  "success": true,
  "message": "People retrieved successfully",
  "data": {
    "items": [
      {
        "id": "uuid-here",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "date_of_birth": "1990-01-15",
        "address": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
        "country": "United States",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "current_employment": {
          "id": "employment-uuid",
          "position": {
            "id": "position-uuid",
            "title": "Software Engineer",
            "department": {
              "id": "dept-uuid",
              "name": "Engineering"
            }
          },
          "start_date": "2023-01-15",
          "is_active": true,
          "salary": 75000
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### Get Person

```http
GET /api/v1/people/{person_id}
```

Retrieve a specific person by ID.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | string | Person UUID |

#### Response

```json
{
  "success": true,
  "message": "Person retrieved successfully",
  "data": {
    "id": "uuid-here",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "date_of_birth": "1990-01-15",
    "address": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "country": "United States",
    "age": 34,
    "full_name": "John Doe",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "employments": [
      {
        "id": "employment-uuid",
        "position": {
          "id": "position-uuid",
          "title": "Software Engineer",
          "department": {
            "id": "dept-uuid",
            "name": "Engineering"
          }
        },
        "start_date": "2023-01-15",
        "end_date": null,
        "is_active": true,
        "salary": 75000,
        "duration_years": 1.2
      }
    ]
  }
}
```

### Create Person

```http
POST /api/v1/people
```

Create a new person record.

#### Request Body

```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "title": "Dr",
  "suffix": "PhD",
  "email": "jane.smith@example.com",
  "phone": "+1-555-987-6543",
  "mobile": "+1-555-987-6544",
  "date_of_birth": "20-06-1985",
  "gender": "Female",
  "marital_status": "Single",
  "address": "456 Oak Ave",
  "city": "Springfield",
  "state": "IL",
  "zip_code": "62702",
  "country": "United States",
  "emergency_contact_name": "John Smith",
  "emergency_contact_phone": "+1-555-123-4567",
  "notes": "Software engineer with 5 years experience",
  "tags": ["engineering", "senior"],
  "status": "active"
}
```

#### Required Fields

- `first_name` (string, 1-100 chars)
- `last_name` (string, 1-100 chars)
- `email` (string, valid email format, unique)

#### Optional Fields

- `title` (string, max 50 chars) - Professional title (e.g., "Dr", "Mr", "Ms")
- `suffix` (string, max 20 chars) - Name suffix (e.g., "Jr", "Sr", "PhD")
- `phone` (string, valid phone format)
- `mobile` (string, valid mobile phone format)
- `date_of_birth` (string, DD-MM-YYYY format)
- `gender` (string, max 20 chars)
- `marital_status` (string, max 20 chars)
- `address` (string, max 500 chars)
- `city` (string, max 100 chars)
- `state` (string, max 100 chars)
- `zip_code` (string, max 20 chars)
- `country` (string, max 100 chars, default: "United States")
- `emergency_contact_name` (string, max 200 chars)
- `emergency_contact_phone` (string, valid phone format)
- `notes` (string, max 2000 chars)
- `tags` (array of strings) - Organizational tags for categorization
- `status` (string, default: "active")

#### Response

```json
{
  "success": true,
  "message": "Person created successfully",
  "data": {
    "id": "new-uuid-here",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    // ... other fields
  }
}
```

### Update Person

```http
PUT /api/v1/people/{person_id}
```

Update an existing person record.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | string | Person UUID |

#### Request Body

Same as create person, but all fields are optional. Only provided fields will be updated.

```json
{
  "phone": "+1-555-999-8888",
  "address": "789 New Street"
}
```

#### Response

```json
{
  "success": true,
  "message": "Person updated successfully",
  "data": {
    // Updated person object
  }
}
```

### Delete Person

```http
DELETE /api/v1/people/{person_id}
```

Delete a person record. This will also delete all associated employment records.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | string | Person UUID |

#### Response

```http
Status: 204 No Content
```

### Search People

```http
GET /api/v1/people/search
```

Advanced search for people with flexible criteria.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (name, email) |
| `department` | string | Department name or ID |
| `position` | string | Position title or ID |
| `city` | string | City name |
| `state` | string | State name |
| `country` | string | Country name |
| `age_min` | integer | Minimum age |
| `age_max` | integer | Maximum age |
| `employed` | boolean | Employment status |
| `salary_min` | number | Minimum salary |
| `salary_max` | number | Maximum salary |

#### Response

Same format as List People endpoint.

## Departments Endpoints

Manage organizational departments.

### List Departments

```http
GET /api/v1/departments
```

Retrieve all departments.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Items per page |
| `search` | string | Search in department name |
| `sort_by` | string | Sort field: "name", "created_at" |
| `include_stats` | boolean | Include position and employee counts |

#### Response

```json
{
  "success": true,
  "message": "Departments retrieved successfully",
  "data": {
    "items": [
      {
        "id": "dept-uuid",
        "name": "Engineering",
        "description": "Software development and engineering",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "position_count": 15,
        "active_employee_count": 42
      }
    ],
    "pagination": {
      // ... pagination info
    }
  }
}
```

### Get Department

```http
GET /api/v1/departments/{department_id}
```

Retrieve a specific department with its positions.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `department_id` | string | Department UUID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_positions` | boolean | Include department positions |
| `include_employees` | boolean | Include employee details |

#### Response

```json
{
  "success": true,
  "message": "Department retrieved successfully",
  "data": {
    "id": "dept-uuid",
    "name": "Engineering",
    "description": "Software development and engineering",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "positions": [
      {
        "id": "position-uuid",
        "title": "Software Engineer",
        "description": "Develop and maintain software applications",
        "employee_count": 8
      }
    ],
    "statistics": {
      "total_positions": 15,
      "total_employees": 42,
      "average_salary": 75000,
      "salary_range": {
        "min": 45000,
        "max": 120000
      }
    }
  }
}
```

### Create Department

```http
POST /api/v1/departments
```

Create a new department.

#### Request Body

```json
{
  "name": "Marketing",
  "description": "Marketing and promotional activities"
}
```

#### Required Fields

- `name` (string, 1-100 chars, unique)

#### Optional Fields

- `description` (string, max 1000 chars)

#### Response

```json
{
  "success": true,
  "message": "Department created successfully",
  "data": {
    "id": "new-dept-uuid",
    "name": "Marketing",
    "description": "Marketing and promotional activities",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

### Update Department

```http
PUT /api/v1/departments/{department_id}
```

Update an existing department.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `department_id` | string | Department UUID |

#### Request Body

```json
{
  "description": "Updated department description"
}
```

### Delete Department

```http
DELETE /api/v1/departments/{department_id}
```

Delete a department. This will also delete all positions and employment records in the department.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `department_id` | string | Department UUID |

#### Response

```http
Status: 204 No Content
```

## Positions Endpoints

Manage job positions within departments.

### List Positions

```http
GET /api/v1/positions
```

Retrieve all positions across departments.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `department_id` | string | Filter by department |
| `search` | string | Search in position title |
| `has_employees` | boolean | Filter by employment status |

#### Response

```json
{
  "success": true,
  "message": "Positions retrieved successfully",
  "data": {
    "items": [
      {
        "id": "position-uuid",
        "title": "Software Engineer",
        "description": "Develop and maintain software applications",
        "department": {
          "id": "dept-uuid",
          "name": "Engineering"
        },
        "employee_count": 8,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

### Get Position

```http
GET /api/v1/positions/{position_id}
```

Retrieve a specific position with current employees.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `position_id` | string | Position UUID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_employees` | boolean | Include current employees |

#### Response

```json
{
  "success": true,
  "message": "Position retrieved successfully",
  "data": {
    "id": "position-uuid",
    "title": "Software Engineer",
    "description": "Develop and maintain software applications",
    "department": {
      "id": "dept-uuid",
      "name": "Engineering"
    },
    "current_employees": [
      {
        "id": "employment-uuid",
        "person": {
          "id": "person-uuid",
          "first_name": "John",
          "last_name": "Doe",
          "email": "john.doe@example.com"
        },
        "start_date": "2023-01-15",
        "salary": 75000
      }
    ],
    "statistics": {
      "total_employees": 8,
      "average_tenure_years": 2.5,
      "average_salary": 75000
    }
  }
}
```

### Create Position

```http
POST /api/v1/positions
```

Create a new position within a department.

#### Request Body

```json
{
  "title": "Senior Software Engineer",
  "description": "Lead software development projects",
  "department_id": "dept-uuid"
}
```

#### Required Fields

- `title` (string, 1-150 chars)
- `department_id` (string, valid department UUID)

#### Optional Fields

- `description` (string, max 1000 chars)

#### Response

```json
{
  "success": true,
  "message": "Position created successfully",
  "data": {
    "id": "new-position-uuid",
    "title": "Senior Software Engineer",
    "description": "Lead software development projects",
    "department": {
      "id": "dept-uuid",
      "name": "Engineering"
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

### Update Position

```http
PUT /api/v1/positions/{position_id}
```

Update an existing position.

### Delete Position

```http
DELETE /api/v1/positions/{position_id}
```

Delete a position. This will also delete all employment records for this position.

## Employment Endpoints

Manage employment relationships between people and positions.

### List Employment Records

```http
GET /api/v1/employment
```

Retrieve employment records with filtering options.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | string | Filter by person |
| `position_id` | string | Filter by position |
| `department_id` | string | Filter by department |
| `is_active` | boolean | Filter by active status |
| `start_date_after` | string | Filter by start date |
| `salary_min` | number | Minimum salary filter |
| `salary_max` | number | Maximum salary filter |

#### Response

```json
{
  "success": true,
  "message": "Employment records retrieved successfully",
  "data": {
    "items": [
      {
        "id": "employment-uuid",
        "person": {
          "id": "person-uuid",
          "first_name": "John",
          "last_name": "Doe",
          "email": "john.doe@example.com"
        },
        "position": {
          "id": "position-uuid",
          "title": "Software Engineer",
          "department": {
            "id": "dept-uuid",
            "name": "Engineering"
          }
        },
        "start_date": "2023-01-15",
        "end_date": null,
        "is_active": true,
        "salary": 75000,
        "duration_years": 1.2,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

### Get Employment Record

```http
GET /api/v1/employment/{employment_id}
```

Retrieve a specific employment record.

### Create Employment Record

```http
POST /api/v1/employment
```

Create a new employment relationship.

#### Request Body

```json
{
  "person_id": "person-uuid",
  "position_id": "position-uuid",
  "start_date": "2024-01-15",
  "salary": 80000,
  "is_active": true
}
```

#### Required Fields

- `person_id` (string, valid person UUID)
- `position_id` (string, valid position UUID)
- `start_date` (string, ISO date format)

#### Optional Fields

- `end_date` (string, ISO date format)
- `is_active` (boolean, default: true)
- `salary` (number, positive value)

### Update Employment Record

```http
PUT /api/v1/employment/{employment_id}
```

Update an existing employment record (e.g., salary changes, promotions).

### Terminate Employment

```http
POST /api/v1/employment/{employment_id}/terminate
```

Terminate an active employment relationship.

#### Request Body

```json
{
  "end_date": "2024-01-31",
  "reason": "Resignation"
}
```

#### Response

```json
{
  "success": true,
  "message": "Employment terminated successfully",
  "data": {
    "id": "employment-uuid",
    "is_active": false,
    "end_date": "2024-01-31",
    // ... other fields
  }
}
```

## Statistics Endpoints

Retrieve various statistics and analytics about the organization.

### Overview Statistics

```http
GET /api/v1/statistics/overview
```

Get high-level organizational statistics.

#### Response

```json
{
  "success": true,
  "message": "Overview statistics retrieved successfully",
  "data": {
    "totals": {
      "people": 150,
      "departments": 5,
      "positions": 25,
      "active_employees": 142,
      "inactive_employees": 8
    },
    "employment": {
      "average_tenure_years": 3.2,
      "turnover_rate_percent": 8.5,
      "new_hires_this_month": 5,
      "terminations_this_month": 2
    },
    "compensation": {
      "average_salary": 72500,
      "median_salary": 68000,
      "salary_range": {
        "min": 35000,
        "max": 150000
      }
    },
    "departments": [
      {
        "name": "Engineering",
        "employee_count": 45,
        "average_salary": 85000
      }
    ]
  }
}
```

### Department Statistics

```http
GET /api/v1/statistics/departments
```

Get detailed statistics for all departments.

#### Response

```json
{
  "success": true,
  "message": "Department statistics retrieved successfully",
  "data": {
    "departments": [
      {
        "id": "dept-uuid",
        "name": "Engineering",
        "statistics": {
          "total_positions": 8,
          "total_employees": 45,
          "average_salary": 85000,
          "median_salary": 82000,
          "salary_range": {
            "min": 60000,
            "max": 150000
          },
          "average_tenure_years": 4.2,
          "turnover_rate_percent": 6.2
        }
      }
    ]
  }
}
```

### Salary Analytics

```http
GET /api/v1/statistics/salaries
```

Get salary distribution and analytics.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `department_id` | string | Filter by department |
| `position_id` | string | Filter by position |
| `group_by` | string | Group by: "department", "position" |

#### Response

```json
{
  "success": true,
  "message": "Salary analytics retrieved successfully",
  "data": {
    "overall": {
      "count": 142,
      "average": 72500,
      "median": 68000,
      "std_deviation": 15200,
      "percentiles": {
        "p25": 55000,
        "p50": 68000,
        "p75": 85000,
        "p90": 105000,
        "p95": 125000
      }
    },
    "by_department": [
      {
        "department": "Engineering",
        "count": 45,
        "average": 85000,
        "median": 82000
      }
    ],
    "distribution": {
      "ranges": [
        {"min": 30000, "max": 50000, "count": 12},
        {"min": 50000, "max": 70000, "count": 45},
        {"min": 70000, "max": 90000, "count": 52},
        {"min": 90000, "max": 110000, "count": 25},
        {"min": 110000, "max": 200000, "count": 8}
      ]
    }
  }
}
```

### Hiring Trends

```http
GET /api/v1/statistics/hiring-trends
```

Get hiring and termination trends over time.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | Period: "month", "quarter", "year" |
| `start_date` | string | Start date (ISO format) |
| `end_date` | string | End date (ISO format) |

#### Response

```json
{
  "success": true,
  "message": "Hiring trends retrieved successfully",
  "data": {
    "trends": [
      {
        "period": "2024-01",
        "hires": 8,
        "terminations": 3,
        "net_change": 5,
        "turnover_rate": 2.1
      }
    ],
    "summary": {
      "total_hires": 45,
      "total_terminations": 18,
      "net_growth": 27,
      "average_monthly_turnover": 1.8
    }
  }
}
```

## Admin Endpoints

Administrative endpoints for system management (requires admin privileges).

### System Health

```http
GET /api/v1/admin/health
```

Get detailed system health information.

#### Response

```json
{
  "success": true,
  "message": "System health retrieved successfully",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "uptime_seconds": 86400,
    "version": "1.0.0",
    "components": {
      "database": {
        "status": "healthy",
        "connection_pool": {
          "active": 5,
          "idle": 15,
          "max": 20
        },
        "query_performance": {
          "avg_response_time_ms": 15.2,
          "slow_queries": 0
        }
      },
      "cache": {
        "status": "healthy",
        "hit_rate": 0.89,
        "memory_usage": "45MB"
      }
    },
    "metrics": {
      "requests_per_minute": 150,
      "error_rate": 0.02,
      "response_time_p95": 250
    }
  }
}
```

### Database Operations

```http
POST /api/v1/admin/database/vacuum
```

Perform database maintenance operations.

```http
GET /api/v1/admin/database/stats
```

Get database statistics and performance metrics.

### User Management

```http
GET /api/v1/admin/users
POST /api/v1/admin/users
PUT /api/v1/admin/users/{user_id}
DELETE /api/v1/admin/users/{user_id}
```

Manage system users and API keys.

## Client SDK Usage

The system provides SDKs for various programming languages to simplify API integration.

### Python SDK

```python
from people_management_client import PeopleManagementClient

# Initialize client
client = PeopleManagementClient(
    base_url="https://api.yourdomain.com",
    api_key="your-api-key-here"
)

# List people
people = client.people.list(page=1, per_page=20)
print(f"Found {people.pagination.total} people")

# Get specific person
person = client.people.get("person-uuid-here")
print(f"Person: {person.full_name}")

# Create new person
new_person = client.people.create({
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567"
})
print(f"Created person with ID: {new_person.id}")

# Search people
results = client.people.search(
    q="John",
    department="Engineering",
    employed=True
)

# Create employment record
employment = client.employment.create({
    "person_id": new_person.id,
    "position_id": "position-uuid",
    "start_date": "2024-01-15",
    "salary": 75000
})

# Get statistics
stats = client.statistics.overview()
print(f"Total employees: {stats.totals.active_employees}")
```

### JavaScript SDK

```javascript
import { PeopleManagementClient } from 'people-management-js-sdk';

// Initialize client
const client = new PeopleManagementClient({
  baseUrl: 'https://api.yourdomain.com',
  apiKey: 'your-api-key-here'
});

// List people
const people = await client.people.list({ page: 1, perPage: 20 });
console.log(`Found ${people.pagination.total} people`);

// Get specific person
const person = await client.people.get('person-uuid-here');
console.log(`Person: ${person.fullName}`);

// Create new person
const newPerson = await client.people.create({
  firstName: 'Jane',
  lastName: 'Smith',
  email: 'jane.smith@example.com',
  phone: '+1-555-987-6543'
});

// Search people
const results = await client.people.search({
  q: 'Jane',
  department: 'Marketing'
});

// Get statistics
const stats = await client.statistics.overview();
console.log(`Total employees: ${stats.totals.activeEmployees}`);
```

### HTTP Client Libraries

For other languages, use standard HTTP client libraries:

#### cURL Examples

```bash
# List people
curl -H "Authorization: Bearer your-api-key" \
     "https://api.yourdomain.com/api/v1/people?page=1&per_page=20"

# Create person
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"first_name":"John","last_name":"Doe","email":"john@example.com"}' \
     "https://api.yourdomain.com/api/v1/people"

# Get statistics
curl -H "Authorization: Bearer your-api-key" \
     "https://api.yourdomain.com/api/v1/statistics/overview"
```

## Examples

### Common Use Cases

#### 1. Employee Onboarding Workflow

```python
# 1. Create person record
person = client.people.create({
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice.johnson@company.com",
    "phone": "+1-555-246-8135",
    "address": "123 Corporate Blvd",
    "city": "Business City",
    "state": "CA",
    "zip_code": "90210"
})

# 2. Find appropriate position
positions = client.positions.list(department_id="engineering-dept-uuid")
position = positions.items[0]  # Select position

# 3. Create employment record
employment = client.employment.create({
    "person_id": person.id,
    "position_id": position.id,
    "start_date": "2024-02-01",
    "salary": 85000,
    "is_active": True
})

# 4. Send welcome notification (if implemented)
# client.notifications.send_welcome_email(person.id)

print(f"Successfully onboarded {person.full_name} as {position.title}")
```

#### 2. Department Reorganization

```python
# 1. Get current department structure
departments = client.departments.list(include_stats=True)
old_dept = next(d for d in departments.items if d.name == "Old Department")

# 2. Create new department
new_dept = client.departments.create({
    "name": "New Department",
    "description": "Reorganized department structure"
})

# 3. Move positions to new department
for position in old_dept.positions:
    client.positions.update(position.id, {
        "department_id": new_dept.id
    })

# 4. Archive old department (if empty)
if old_dept.active_employee_count == 0:
    client.departments.delete(old_dept.id)

print(f"Reorganization complete: moved {len(old_dept.positions)} positions")
```

#### 3. Salary Analysis Report

```python
# 1. Get overall salary statistics
salary_stats = client.statistics.salaries()

# 2. Get department-specific data
dept_stats = client.statistics.departments()

# 3. Generate report
report = {
    "overall_stats": {
        "average_salary": salary_stats.overall.average,
        "median_salary": salary_stats.overall.median,
        "total_employees": salary_stats.overall.count
    },
    "department_breakdown": []
}

for dept in dept_stats.departments:
    report["department_breakdown"].append({
        "department": dept.name,
        "employee_count": dept.statistics.total_employees,
        "average_salary": dept.statistics.average_salary,
        "salary_range": dept.statistics.salary_range
    })

# 4. Export to CSV or other format
import csv
with open('salary_report.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['department', 'employee_count', 'average_salary'])
    writer.writeheader()
    for dept in report["department_breakdown"]:
        writer.writerow(dept)

print("Salary analysis report generated successfully")
```

#### 4. Employee Search and Filtering

```python
# Complex search example
search_criteria = {
    "q": "software engineer",  # Search in names and positions
    "department": "Engineering",
    "salary_min": 70000,
    "employed": True,
    "city": "San Francisco"
}

results = client.people.search(**search_criteria)

print(f"Found {len(results.items)} employees matching criteria:")
for person in results.items:
    employment = person.current_employment
    print(f"- {person.full_name}: {employment.position.title} (${employment.salary:,})")
```

#### 5. Bulk Data Import

```python
import csv

# Read employee data from CSV
employees_to_import = []
with open('new_employees.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        employees_to_import.append({
            "first_name": row['first_name'],
            "last_name": row['last_name'],
            "email": row['email'],
            "phone": row['phone'],
            "department": row['department'],
            "position": row['position'],
            "salary": float(row['salary']),
            "start_date": row['start_date']
        })

# Import employees
success_count = 0
error_count = 0

for emp_data in employees_to_import:
    try:
        # Create person
        person = client.people.create({
            "first_name": emp_data["first_name"],
            "last_name": emp_data["last_name"],
            "email": emp_data["email"],
            "phone": emp_data["phone"]
        })
        
        # Find department and position
        departments = client.departments.list(search=emp_data["department"])
        department = departments.items[0]
        
        positions = client.positions.list(
            department_id=department.id,
            search=emp_data["position"]
        )
        position = positions.items[0]
        
        # Create employment
        client.employment.create({
            "person_id": person.id,
            "position_id": position.id,
            "start_date": emp_data["start_date"],
            "salary": emp_data["salary"]
        })
        
        success_count += 1
        print(f"✓ Imported {person.full_name}")
        
    except Exception as e:
        error_count += 1
        print(f"✗ Failed to import {emp_data['first_name']} {emp_data['last_name']}: {e}")

print(f"\nImport complete: {success_count} successful, {error_count} errors")
```

### Error Handling Examples

```python
from people_management_client import PeopleManagementClient, APIError, ValidationError

client = PeopleManagementClient(
    base_url="https://api.yourdomain.com",
    api_key="your-api-key"
)

try:
    # Attempt to create person with invalid data
    person = client.people.create({
        "first_name": "",  # Invalid: empty name
        "last_name": "Doe",
        "email": "invalid-email"  # Invalid: bad email format
    })
except ValidationError as e:
    print("Validation failed:")
    for field, errors in e.field_errors.items():
        print(f"  {field}: {', '.join(errors)}")
except APIError as e:
    if e.status_code == 409:
        print("Person already exists")
    elif e.status_code == 429:
        print("Rate limit exceeded, please wait")
    else:
        print(f"API error: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Pagination Handling

```python
# Get all people using pagination
all_people = []
page = 1
per_page = 50

while True:
    result = client.people.list(page=page, per_page=per_page)
    all_people.extend(result.items)
    
    if not result.pagination.has_next:
        break
    
    page += 1

print(f"Retrieved {len(all_people)} total people across {page} pages")

# Alternative: Using iterator (if SDK supports it)
for person in client.people.iterate():
    print(f"Processing {person.full_name}")
    # Process each person
```

This comprehensive API documentation provides all the information needed to integrate with the People Management System API effectively. The examples demonstrate common use cases and best practices for using the API in real-world scenarios.