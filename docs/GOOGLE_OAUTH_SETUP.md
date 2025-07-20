# Google OAuth Authentication Setup Guide

**Author:** AI Assistant
**Status:** Ready for Implementation
**Created:** 2025-01-27
**Related:** [Authentication Implementation Plan](implementation/authentication_plan.md)

---

## Overview

This guide provides step-by-step instructions for configuring Google OAuth authentication in the Reactrine application. The implementation supports both new user registration and existing user login through Google accounts.

## Prerequisites

- Google Cloud Platform account
- Domain name or localhost setup for development
- Backend and frontend applications running

## 1. Google Cloud Console Setup

### Step 1.1: Create or Select a Google Cloud Project

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Either create a new project or select an existing one
3. Note your project ID for reference

### Step 1.2: Enable Required APIs

1. Go to **APIs & Services** → **Library**
2. Search for and enable the following APIs:
   - **Google Identity Services** (for OAuth2 authentication and user profile information)

### Step 1.3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** for user type (unless you have a Google Workspace)
3. Fill in the required information:
   - **App name**: Your application name (e.g., "Reactrine App")
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Add scopes (recommended):
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
5. Add test users if still in development mode

### Step 1.4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Choose **Web application** as the application type
4. Configure the following:

   **For Development:**

   ```
   Name: Reactrine Development
   Authorized JavaScript origins:
   - http://localhost:3000
   - http://127.0.0.1:3000

   Authorized redirect URIs:
   - http://localhost:3000
   - http://127.0.0.1:3000
   ```

   **For Production:**

   ```
   Name: Reactrine Production
   Authorized JavaScript origins:
   - https://yourdomain.com
   - https://www.yourdomain.com

   Authorized redirect URIs:
   - https://yourdomain.com
   - https://www.yourdomain.com
   ```

5. Save and note down the **Client ID** and **Client Secret**

## 2. Backend Configuration

### Step 2.1: Update Environment Files

Update the Google OAuth settings in your environment configuration files:

**config/common.env:**

```env
# Google OAuth (replace with actual values)
GOOGLE_OAUTH_CLIENT_ID=your_actual_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_actual_google_client_secret_here
```

**config/dev.env:**

```env
# Development-specific Google OAuth settings
GOOGLE_OAUTH_CLIENT_ID=your_dev_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_dev_google_client_secret_here
```

**config/prod.env:**

```env
# Production Google OAuth settings
GOOGLE_OAUTH_CLIENT_ID=your_prod_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_prod_google_client_secret_here
```

### Step 2.2: Secure Secrets Management

For production environments, use the secrets management system:

1. Create secret files in the `secrets/` directory:

   ```bash
   echo "your_actual_google_client_id" > secrets/google_oauth_client_id.txt
   echo "your_actual_google_client_secret" > secrets/google_oauth_client_secret.txt
   ```

2. Update `backend/app/core/config.py` to use secrets (if not already configured):
   ```python
   GOOGLE_OAUTH_CLIENT_ID: str = Field(
       default="",
       description="Google OAuth Client ID"
   )
   GOOGLE_OAUTH_CLIENT_SECRET: str = Field(
       default="",
       description="Google OAuth Client Secret"
   )
   ```

## 3. Frontend Configuration

### Step 3.1: Set Frontend Environment Variable

The frontend needs the Google OAuth Client ID to initialize the Google OAuth provider.

**For Development (using environment variables):**

```bash
export VITE_GOOGLE_OAUTH_CLIENT_ID="your_actual_google_client_id_here"
```

**For Production (in your deployment configuration):**
Set the environment variable in your deployment platform:

```env
VITE_GOOGLE_OAUTH_CLIENT_ID=your_actual_google_client_id_here
```

### Step 3.2: Update Vite Configuration (Alternative)

If you prefer to hardcode for specific environments, update `frontend/vite.config.ts`:

```typescript
export default defineConfig({
  // ... other config
  define: {
    "import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID": JSON.stringify(
      process.env.VITE_GOOGLE_OAUTH_CLIENT_ID || "your_actual_client_id_here"
    ),
  },
  // ... rest of config
});
```

## 4. Deployment Configuration

### Step 4.1: Docker Environment

If using Docker, update your `docker-compose.yml` or environment files:

```yaml
services:
  frontend:
    environment:
      - VITE_GOOGLE_OAUTH_CLIENT_ID=${VITE_GOOGLE_OAUTH_CLIENT_ID}

  backend:
    environment:
      - GOOGLE_OAUTH_CLIENT_ID=${GOOGLE_OAUTH_CLIENT_ID}
      - GOOGLE_OAUTH_CLIENT_SECRET=${GOOGLE_OAUTH_CLIENT_SECRET}
```

### Step 4.2: Production Deployment

For production deployments, ensure:

1. **HTTPS is enabled** - Google OAuth requires HTTPS in production
2. **Domain verification** - Your domain must be verified in Google Cloud Console
3. **Environment variables are set** in your hosting platform
4. **CORS settings** are properly configured for your domain

## 5. Testing the Integration

### Step 5.1: Development Testing

1. Start your development environment:

   ```bash
   just dev
   ```

2. Navigate to `http://localhost:3000/login`
3. You should see a "Sign in with Google" button
4. Click the button to test the OAuth flow

### Step 5.2: Verify Backend Integration

Test the backend endpoint directly:

```bash
# Test the Google OAuth endpoint (replace with actual token)
curl -X POST http://localhost:8000/api/v1/auth/google \
  -H "Content-Type: application/json" \
  -d '{"credential": "your_test_google_jwt_token"}'
```

## 6. Security Considerations

### 6.1: Client ID Security

- **Frontend Client ID**: Can be public as it's included in the frontend bundle
- **Client Secret**: Must be kept secure and only used in the backend
- Never commit actual credentials to version control

### 6.2: Domain Security

- Always use HTTPS in production
- Configure proper CORS settings
- Restrict authorized domains to your actual domains

### 6.3: User Registration Control

The implementation respects the `ALLOW_REGISTRATION` setting:

- If `ALLOW_REGISTRATION=false`, existing Google users can log in but new users cannot register
- If `ALLOW_REGISTRATION=true`, new Google users will automatically get accounts created

## 7. Troubleshooting

### Common Issues and Solutions

**Issue: "Error 400: redirect_uri_mismatch"**

- **Solution**: Ensure your redirect URIs in Google Cloud Console exactly match your application URLs

**Issue: "Error 400: invalid_request"**

- **Solution**: Check that your Client ID is correctly configured in both frontend and backend

**Issue: Google button not appearing**

- **Solution**: Verify `VITE_GOOGLE_OAUTH_CLIENT_ID` is set and the frontend has been rebuilt

**Issue: "Invalid Google token" error**

- **Solution**: Check that the Client ID in the backend matches the one used to generate the token

**Issue: Registration disabled for new Google users**

- **Solution**: Set `ALLOW_REGISTRATION=true` in your environment configuration

### Debug Mode

Enable debug logging in the backend to troubleshoot OAuth issues:

```python
# In backend/app/core/logging.py or your logging configuration
import logging
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

## 8. Production Checklist

Before deploying to production:

- [ ] Google Cloud Console project is set up for production
- [ ] OAuth consent screen is configured and approved (if needed)
- [ ] Production domains are added to authorized origins
- [ ] HTTPS is enabled on your domain
- [ ] Environment variables are set in production environment
- [ ] Client Secret is securely stored (not in code)
- [ ] CORS is properly configured
- [ ] Registration settings are configured as desired
- [ ] Test the complete OAuth flow in production environment

## 9. Monitoring and Maintenance

### 9.1: Monitoring OAuth Usage

Monitor Google OAuth usage in:

- Google Cloud Console → APIs & Services → Quotas
- Your application logs for authentication errors
- User registration/login analytics

### 9.2: Token Management

The implementation uses short-lived access tokens (15 minutes by default):

- No refresh tokens are stored
- Users will need to re-authenticate after token expiry
- Consider implementing longer sessions if needed for your use case

## 10. Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Websites](https://developers.google.com/identity/sign-in/web)
- [@react-oauth/google Documentation](https://github.com/MomenSherif/react-oauth)
- [Reactrine Authentication Plan](implementation/authentication_plan.md)

---

## Support

If you encounter issues with Google OAuth setup:

1. Check the troubleshooting section above
2. Verify all configuration steps have been completed
3. Check the application logs for specific error messages
4. Consult the Google Cloud Console for OAuth-specific errors

Remember to keep your Client Secret secure and never commit it to version control!
