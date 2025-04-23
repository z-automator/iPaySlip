# Leaves Management API

This Django app provides a REST API for managing employee leave requests in the HR system.

## Features

- Full CRUD operations for leave requests
- Permission-based access control
- Validation for leave dates
- Prevention of overlapping leave dates
- Status tracking (pending/approved/rejected)

## API Endpoints

- `GET /api/leaves/` - List all leaves (filterable)
- `POST /api/leaves/` - Create new leave
- `GET /api/leaves/{id}/` - Retrieve a specific leave
- `PUT /api/leaves/{id}/` - Update a leave (full update)
- `PATCH /api/leaves/{id}/` - Partial update a leave
- `DELETE /api/leaves/{id}/` - Delete a leave

## Permissions

- Authentication is required for all endpoints
- Regular users can only access their own leaves
- Staff users can access all leaves
- Only staff users can change the status of a leave request

## Example Request

```json
{
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "leave_type": "vacation",
    "reason": "Family trip"
}
```

## Example Response

```json
{
    "id": 1,
    "employee": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "full_name": "John Doe"
    },
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "leave_type": "vacation",
    "leave_type_display": "Vacation",
    "status": "pending",
    "status_display": "Pending",
    "reason": "Family trip",
    "created_at": "2024-04-16T00:45:00Z",
    "updated_at": "2024-04-16T00:45:00Z"
}
```

## Filtering Options

The list endpoint supports filtering by:
- `status` - Filter by status (pending/approved/rejected)
- `leave_type` - Filter by leave type
- `start_date` - Filter by start date
- `end_date` - Filter by end date

Example: `/api/leaves/?status=pending&leave_type=vacation`
