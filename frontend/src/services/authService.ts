// Generated API client imports
import {
  AuthService,
  type Body_login_user_api_v1_auth_login_post,
  type CSRFToken as GeneratedCSRFToken,
  type RegistrationStatus as GeneratedRegistrationStatus,
  type User as GeneratedUser,
  type GoogleLoginRequest,
  type UserCreate,
} from '@/lib/api-client';

// Import our own User type that includes role
import type { User } from '../types/api';

interface RegistrationStatus {
  allowed: boolean;
  message?: string;
}

// All methods now use the generated client
export const checkRegistrationStatus = async (): Promise<RegistrationStatus> => {
  const response: GeneratedRegistrationStatus =
    await AuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet();
  return {
    allowed: response.allowed,
    message: response.message || undefined,
  };
};

export const register = async (email: string, password: string): Promise<User> => {
  // First check if registration is allowed
  const status = await checkRegistrationStatus();
  if (!status.allowed) {
    throw new Error(status.message || 'Registration is currently disabled');
  }

  const requestBody: UserCreate = {
    email,
    password,
    auth_provider: 'email',
  };

  const response: GeneratedUser = await AuthService.registerUserApiV1AuthRegisterPost({
    requestBody,
  });

  return {
    id: response.id,
    email: response.email,
    auth_provider: response.auth_provider,
    is_active: response.is_active,
    role: response.role
      ? {
          name: response.role.name,
          description: response.role.description || null,
        }
      : null,
    created_at: response.created_at,
    updated_at: response.updated_at,
  };
};

export const login = async (email: string, password: string): Promise<User> => {
  const formData: Body_login_user_api_v1_auth_login_post = {
    username: email, // OAuth2 standard uses 'username' field
    password: password,
  };

  const response: GeneratedUser = await AuthService.loginUserApiV1AuthLoginPost({
    formData,
  });

  return {
    id: response.id,
    email: response.email,
    auth_provider: response.auth_provider,
    is_active: response.is_active,
    role: response.role
      ? {
          name: response.role.name,
          description: response.role.description || null,
        }
      : null,
    created_at: response.created_at,
    updated_at: response.updated_at,
  };
};

export const loginWithGoogle = async (credential: string): Promise<User> => {
  const requestBody: GoogleLoginRequest = {
    credential,
  };

  const response: GeneratedUser =
    await AuthService.googleOauthCallbackApiV1AuthGooglePost({
      requestBody,
    });

  return {
    id: response.id,
    email: response.email,
    auth_provider: response.auth_provider,
    is_active: response.is_active,
    role: response.role
      ? {
          name: response.role.name,
          description: response.role.description || null,
        }
      : null,
    created_at: response.created_at,
    updated_at: response.updated_at,
  };
};

export const getCurrentUser = async (): Promise<User> => {
  const response: GeneratedUser = await AuthService.getCurrentUserInfoApiV1AuthMeGet();

  return {
    id: response.id,
    email: response.email,
    auth_provider: response.auth_provider,
    is_active: response.is_active,
    role: response.role
      ? {
          name: response.role.name,
          description: response.role.description || null,
        }
      : null,
    created_at: response.created_at,
    updated_at: response.updated_at,
  };
};

export const logout = async (): Promise<void> => {
  // The generated client expects a refresh token parameter, but we're using cookie-based auth
  // Pass undefined/null as the refresh token since cookies handle the session
  await AuthService.logoutUserApiV1AuthLogoutPost({
    refreshToken: undefined,
  });
};

export const getCsrfToken = async (): Promise<string> => {
  const response: GeneratedCSRFToken =
    await AuthService.getCsrfTokenApiV1AuthCsrfTokenGet();
  return response.token;
};

// CSRF token initialization is now handled by the generated client configuration
export const initializeCsrfToken = async (): Promise<void> => {
  // This is now handled by the generated client configuration
  // but we keep this function for backward compatibility
  try {
    await getCsrfToken();
  } catch (error) {
    console.warn('Failed to initialize CSRF token:', error);
  }
};

export default {
  checkRegistrationStatus,
  register,
  login,
  loginWithGoogle,
  getCurrentUser,
  logout,
  getCsrfToken,
  initializeCsrfToken,
};
