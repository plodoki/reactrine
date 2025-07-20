# User Authentication

The Reactrine provides a comprehensive and secure user authentication system out of the box. It supports both traditional email/password registration and social login via Google, offering a flexible and modern user experience.

## Authentication Methods

- **Email & Password:** Users can sign up and log in using a unique email address and a secure password.
- **Google OAuth 2.0:** Users can opt for a one-click registration and login process using their existing Google account.

## Security Features

Security is a top priority in the authentication system, which incorporates several best practices:

- **Secure Password Hashing:** All passwords are run through the `bcrypt` hashing algorithm before being stored in the database. This ensures that even if the database is compromised, the original passwords cannot be easily recovered.
- **HttpOnly Cookies for Session Management:** After a successful login, the server issues a JSON Web Token (JWT) that is stored in an `HttpOnly` cookie. This is a critical security measure that prevents the token from being accessed by client-side JavaScript, mitigating the risk of Cross-Site Scripting (XSS) attacks.
- **CSRF Protection:** The system employs a double-submit cookie pattern to protect against Cross-Site Request Forgery (CSRF) attacks. A separate, non-HttpOnly cookie containing a CSRF token is sent to the client, and this token must be included as a header in all subsequent state-changing requests.
- **Secure Cookie Attributes:** All session-related cookies are set with the `Secure` and `SameSite=Lax` attributes, ensuring they are only sent over HTTPS and providing additional protection against CSRF attacks.

## How It Works

The authentication flow is designed to be both secure and user-friendly.

1.  **Registration/Login:** The user signs up or logs in via the frontend application.
2.  **Token Issuance:** Upon successful authentication, the FastAPI backend generates a JWT and a CSRF token.
3.  **Cookie Setting:** The backend sets the JWT in a secure, `HttpOnly` cookie and the CSRF token in a separate, accessible cookie.
4.  **Authenticated Requests:** For subsequent requests to protected API endpoints, the browser automatically sends the JWT cookie. The frontend API client is configured to read the CSRF token from its cookie and include it as a request header.
5.  **Server-Side Verification:** The backend verifies both the JWT and the CSRF token before granting access to the protected resource.

## Disabling User Registration

For applications that require manual user provisioning or are intended for a closed group of users, you can disable new user registrations by setting the following environment variable:

```
ALLOW_REGISTRATION=false
```

When this is set to `false`, the registration endpoint will be disabled, and the frontend will display a message indicating that new registrations are not being accepted.

This robust authentication system provides a solid foundation for building secure web applications, allowing you to focus on your application's core features.
