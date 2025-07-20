# Role-Based Access Control (RBAC)

The Reactrine includes a foundational Role-Based Access Control (RBAC) system designed for both simplicity and extensibility. It provides a straightforward way to protect administrative functions while offering a clear path for implementing more granular permissions as your application grows.

## Core Concepts

The RBAC system is built on a few core principles:

- **Simplicity:** The initial setup is minimal, focusing on two essential roles to get you started quickly.
- **Extensibility:** The architecture is designed to accommodate more complex permission systems in the future without requiring a major overhaul.
- **Security:** The system is designed to prevent common security vulnerabilities like privilege escalation and unauthorized data access.

### Default Roles

The boilerplate comes with two pre-defined roles:

- **Admin:** This role grants full access to all system features, including user management and system configuration.
- **User:** This is the default role assigned to all new users, providing access to standard application features.

Each user is assigned a single role, which simplifies the permission model and makes it easy to manage user access.

## Implementation Details

The RBAC system is implemented using a combination of database models, repository patterns, and FastAPI dependencies.

### Database Schema

The `Role` model is defined in `backend/app/models/role.py` and is linked to the `User` model via a foreign key. This establishes a one-to-many relationship between roles and users (one role can be assigned to many users).

During the initial database migration, two default roles (`admin` and `user`) are automatically created and seeded in the `role` table.

### API Endpoint Protection

API endpoints are protected using a `RoleRequired` dependency, which is implemented in `backend/app/api/rbac.py`. This dependency checks the role of the current user and ensures they have the necessary permissions to access a given endpoint.

Here's how you can protect an endpoint to be accessible only by administrators:

```python
from app.api.deps import AdminRequired

@router.get("/admin/users", dependencies=[Depends(AdminRequired)])
async def list_users():
    # This endpoint is now protected and only accessible by users with the 'admin' role.
    return {"users": [...]}
```

### Initial Admin User

You can designate an initial admin user by setting the `INITIAL_ADMIN_EMAIL` environment variable. During the application's startup, a script will automatically find the user with that email address and assign them the 'admin' role.

## Frontend Integration

The frontend is designed to be aware of user roles, allowing you to create different user experiences based on their permissions.

### Role-Based UI Components

The application's state management (powered by Zustand) includes information about the current user's role. This allows you to conditionally render UI components based on whether the user is an administrator.

For example, you can show a link to the admin dashboard only to users with the 'admin' role:

```typescript
// Example of a conditionally rendered menu item
{
  isAdmin && (
    <MenuItem component={Link} to="/admin/users">
      User Management
    </MenuItem>
  );
}
```

### Protected Routes

The frontend routing is also configured to protect entire sections of the application. The `ProtectedRoute` component ensures that only users with the specified roles can access certain routes.

```typescript
// Protect admin routes
<ProtectedRoute roles={["admin"]}>
  <Route path="/admin/*" element={<AdminLayout />} />
</ProtectedRoute>
```

This combination of backend and frontend controls provides a robust and secure RBAC system that you can easily extend to meet the needs of your application.
