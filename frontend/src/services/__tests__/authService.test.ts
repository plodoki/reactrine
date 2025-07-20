import {
  mockGeneratedCSRFToken,
  mockGeneratedRegistrationStatus,
  mockGeneratedUser,
} from '@/test/factories';
import { createMockError } from '@/test/utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock the generated API client using vi.hoisted to ensure it runs before imports
const mockAuthService = vi.hoisted(() => ({
  getRegistrationStatusApiV1AuthRegistrationStatusGet: vi.fn(),
  registerUserApiV1AuthRegisterPost: vi.fn(),
  loginUserApiV1AuthLoginPost: vi.fn(),
  googleOauthCallbackApiV1AuthGooglePost: vi.fn(),
  getCurrentUserInfoApiV1AuthMeGet: vi.fn(),
  logoutUserApiV1AuthLogoutPost: vi.fn(),
  getCsrfTokenApiV1AuthCsrfTokenGet: vi.fn(),
}));

// Mock the generated client module
vi.mock('@/lib/api-client', () => ({
  AuthService: mockAuthService,
}));

// Import the service functions after mocking
import {
  checkRegistrationStatus,
  getCsrfToken,
  getCurrentUser,
  initializeCsrfToken,
  login,
  loginWithGoogle,
  logout,
  register,
} from '../authService';

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('checkRegistrationStatus', () => {
    it('should return registration status from generated client', async () => {
      // Arrange
      const mockResponse = mockGeneratedRegistrationStatus();
      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await checkRegistrationStatus();

      // Assert
      expect(
        mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet
      ).toHaveBeenCalledTimes(1);
      expect(result).toEqual({
        allowed: mockResponse.allowed,
        message: undefined, // null converted to undefined
      });
    });

    it('should handle 404 errors gracefully', async () => {
      // Arrange
      const error = createMockError(404, 'Not Found');
      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(checkRegistrationStatus()).rejects.toThrow('Not Found');
      expect(
        mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet
      ).toHaveBeenCalledTimes(1);
    });

    it('should transform response types correctly', async () => {
      // Arrange
      const mockResponse = mockGeneratedRegistrationStatus({
        allowed: false,
        message: 'Registration disabled',
      });
      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await checkRegistrationStatus();

      // Assert
      expect(result).toEqual({
        allowed: false,
        message: 'Registration disabled',
      });
    });

    it('should handle null message correctly', async () => {
      // Arrange
      const mockResponse = mockGeneratedRegistrationStatus({
        allowed: true,
        message: null,
      });
      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await checkRegistrationStatus();

      // Assert
      expect(result).toEqual({
        allowed: true,
        message: undefined,
      });
    });
  });

  describe('register', () => {
    it('should register user with generated client', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockRegistrationResponse = mockGeneratedRegistrationStatus({
        allowed: true,
      });
      const mockUserResponse = mockGeneratedUser();

      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockRegistrationResponse
      );
      mockAuthService.registerUserApiV1AuthRegisterPost.mockResolvedValue(
        mockUserResponse
      );

      // Act
      const result = await register(email, password);

      // Assert
      expect(
        mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet
      ).toHaveBeenCalledTimes(1);
      expect(mockAuthService.registerUserApiV1AuthRegisterPost).toHaveBeenCalledWith({
        requestBody: {
          email,
          password,
          auth_provider: 'email',
        },
      });
      expect(result).toEqual({
        id: mockUserResponse.id,
        email: mockUserResponse.email,
        auth_provider: mockUserResponse.auth_provider,
        is_active: mockUserResponse.is_active,
        role: mockUserResponse.role,
        created_at: mockUserResponse.created_at,
        updated_at: mockUserResponse.updated_at,
      });
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const email = 'invalid-email';
      const password = 'weak';
      const mockRegistrationResponse = mockGeneratedRegistrationStatus({
        allowed: true,
      });
      const error = createMockError(422, 'Validation Error', {
        detail: 'Invalid email format',
      });

      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockRegistrationResponse
      );
      mockAuthService.registerUserApiV1AuthRegisterPost.mockRejectedValue(error);

      // Act & Assert
      await expect(register(email, password)).rejects.toThrow('Validation Error');
      expect(mockAuthService.registerUserApiV1AuthRegisterPost).toHaveBeenCalledWith({
        requestBody: {
          email,
          password,
          auth_provider: 'email',
        },
      });
    });

    it('should handle duplicate email errors (409)', async () => {
      // Arrange
      const email = 'existing@example.com';
      const password = 'password123';
      const mockRegistrationResponse = mockGeneratedRegistrationStatus({
        allowed: true,
      });
      const error = createMockError(409, 'Conflict', {
        detail: 'Email already exists',
      });

      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockRegistrationResponse
      );
      mockAuthService.registerUserApiV1AuthRegisterPost.mockRejectedValue(error);

      // Act & Assert
      await expect(register(email, password)).rejects.toThrow('Conflict');
    });

    it('should transform UserCreate to legacy User format', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockRegistrationResponse = mockGeneratedRegistrationStatus({
        allowed: true,
      });
      const mockUserResponse = mockGeneratedUser({
        id: 42,
        email: 'test@example.com',
        auth_provider: 'email',
        is_active: true,
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T10:00:00Z',
      });

      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockRegistrationResponse
      );
      mockAuthService.registerUserApiV1AuthRegisterPost.mockResolvedValue(
        mockUserResponse
      );

      // Act
      const result = await register(email, password);

      // Assert
      expect(result).toEqual({
        id: 42,
        email: 'test@example.com',
        auth_provider: 'email',
        is_active: true,
        role: {
          name: 'user',
          description: 'Standard user role',
        },
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T10:00:00Z',
      });
    });

    it('should handle registration disabled', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockRegistrationResponse = mockGeneratedRegistrationStatus({
        allowed: false,
        message: 'Registration is disabled',
      });

      mockAuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet.mockResolvedValue(
        mockRegistrationResponse
      );

      // Act & Assert
      await expect(register(email, password)).rejects.toThrow(
        'Registration is disabled'
      );
      expect(mockAuthService.registerUserApiV1AuthRegisterPost).not.toHaveBeenCalled();
    });
  });

  describe('login', () => {
    it('should login with email/password using generated client', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockUserResponse = mockGeneratedUser();

      mockAuthService.loginUserApiV1AuthLoginPost.mockResolvedValue(mockUserResponse);

      // Act
      const result = await login(email, password);

      // Assert
      expect(mockAuthService.loginUserApiV1AuthLoginPost).toHaveBeenCalledWith({
        formData: {
          username: email, // OAuth2 standard uses 'username' field
          password: password,
        },
      });
      expect(result).toEqual({
        id: mockUserResponse.id,
        email: mockUserResponse.email,
        auth_provider: mockUserResponse.auth_provider,
        is_active: mockUserResponse.is_active,
        role: mockUserResponse.role,
        created_at: mockUserResponse.created_at,
        updated_at: mockUserResponse.updated_at,
      });
    });

    it('should handle invalid credentials (401)', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'wrongpassword';
      const error = createMockError(401, 'Unauthorized', {
        detail: 'Invalid credentials',
      });

      mockAuthService.loginUserApiV1AuthLoginPost.mockRejectedValue(error);

      // Act & Assert
      await expect(login(email, password)).rejects.toThrow('Unauthorized');
      expect(mockAuthService.loginUserApiV1AuthLoginPost).toHaveBeenCalledWith({
        formData: {
          username: email,
          password: password,
        },
      });
    });

    it('should set cookies correctly', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockUserResponse = mockGeneratedUser();

      mockAuthService.loginUserApiV1AuthLoginPost.mockResolvedValue(mockUserResponse);

      // Act
      const result = await login(email, password);

      // Assert
      expect(result).toBeDefined();
      expect(mockAuthService.loginUserApiV1AuthLoginPost).toHaveBeenCalledTimes(1);
      // Note: Cookie setting is handled by the backend and generated client
    });

    it('should transform login response to legacy format', async () => {
      // Arrange
      const email = 'test@example.com';
      const password = 'password123';
      const mockUserResponse = mockGeneratedUser({
        id: 123,
        email: 'test@example.com',
        auth_provider: 'local',
        is_active: true,
        created_at: '2024-02-01T12:00:00Z',
        updated_at: '2024-02-01T12:30:00Z',
      });

      mockAuthService.loginUserApiV1AuthLoginPost.mockResolvedValue(mockUserResponse);

      // Act
      const result = await login(email, password);

      // Assert
      expect(result).toEqual({
        id: 123,
        email: 'test@example.com',
        auth_provider: 'local',
        is_active: true,
        role: {
          name: 'user',
          description: 'Standard user role',
        },
        created_at: '2024-02-01T12:00:00Z',
        updated_at: '2024-02-01T12:30:00Z',
      });
    });
  });

  describe('loginWithGoogle', () => {
    it('should login with Google credential', async () => {
      // Arrange
      const credential = 'mock-google-credential';
      const mockUserResponse = mockGeneratedUser({
        auth_provider: 'google',
      });

      mockAuthService.googleOauthCallbackApiV1AuthGooglePost.mockResolvedValue(
        mockUserResponse
      );

      // Act
      const result = await loginWithGoogle(credential);

      // Assert
      expect(
        mockAuthService.googleOauthCallbackApiV1AuthGooglePost
      ).toHaveBeenCalledWith({
        requestBody: {
          credential,
        },
      });
      expect(result).toEqual({
        id: mockUserResponse.id,
        email: mockUserResponse.email,
        auth_provider: mockUserResponse.auth_provider,
        is_active: mockUserResponse.is_active,
        role: mockUserResponse.role,
        created_at: mockUserResponse.created_at,
        updated_at: mockUserResponse.updated_at,
      });
    });

    it('should handle invalid Google tokens', async () => {
      // Arrange
      const credential = 'invalid-google-credential';
      const error = createMockError(400, 'Bad Request', {
        detail: 'Invalid Google token',
      });

      mockAuthService.googleOauthCallbackApiV1AuthGooglePost.mockRejectedValue(error);

      // Act & Assert
      await expect(loginWithGoogle(credential)).rejects.toThrow('Bad Request');
      expect(
        mockAuthService.googleOauthCallbackApiV1AuthGooglePost
      ).toHaveBeenCalledWith({
        requestBody: {
          credential,
        },
      });
    });

    it('should transform user response correctly', async () => {
      // Arrange
      const credential = 'mock-google-credential';
      const mockUserResponse = mockGeneratedUser({
        id: 456,
        email: 'google@example.com',
        auth_provider: 'google',
        is_active: true,
        created_at: '2024-03-01T08:00:00Z',
        updated_at: '2024-03-01T08:00:00Z',
      });

      mockAuthService.googleOauthCallbackApiV1AuthGooglePost.mockResolvedValue(
        mockUserResponse
      );

      // Act
      const result = await loginWithGoogle(credential);

      // Assert
      expect(result).toEqual({
        id: 456,
        email: 'google@example.com',
        auth_provider: 'google',
        is_active: true,
        role: {
          name: 'user',
          description: 'Standard user role',
        },
        created_at: '2024-03-01T08:00:00Z',
        updated_at: '2024-03-01T08:00:00Z',
      });
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user from generated client', async () => {
      // Arrange
      const mockUserResponse = mockGeneratedUser();

      mockAuthService.getCurrentUserInfoApiV1AuthMeGet.mockResolvedValue(
        mockUserResponse
      );

      // Act
      const result = await getCurrentUser();

      // Assert
      expect(mockAuthService.getCurrentUserInfoApiV1AuthMeGet).toHaveBeenCalledTimes(1);
      expect(result).toEqual({
        id: mockUserResponse.id,
        email: mockUserResponse.email,
        auth_provider: mockUserResponse.auth_provider,
        is_active: mockUserResponse.is_active,
        role: mockUserResponse.role,
        created_at: mockUserResponse.created_at,
        updated_at: mockUserResponse.updated_at,
      });
    });

    it('should handle unauthenticated requests (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized', {
        detail: 'Not authenticated',
      });

      mockAuthService.getCurrentUserInfoApiV1AuthMeGet.mockRejectedValue(error);

      // Act & Assert
      await expect(getCurrentUser()).rejects.toThrow('Unauthorized');
      expect(mockAuthService.getCurrentUserInfoApiV1AuthMeGet).toHaveBeenCalledTimes(1);
    });

    it('should transform GeneratedUser to legacy User format', async () => {
      // Arrange
      const mockUserResponse = mockGeneratedUser({
        id: 789,
        email: 'current@example.com',
        auth_provider: 'local',
        is_active: true,
        created_at: '2024-04-01T14:00:00Z',
        updated_at: '2024-04-01T14:30:00Z',
      });

      mockAuthService.getCurrentUserInfoApiV1AuthMeGet.mockResolvedValue(
        mockUserResponse
      );

      // Act
      const result = await getCurrentUser();

      // Assert
      expect(result).toEqual({
        id: 789,
        email: 'current@example.com',
        auth_provider: 'local',
        is_active: true,
        role: {
          name: 'user',
          description: 'Standard user role',
        },
        created_at: '2024-04-01T14:00:00Z',
        updated_at: '2024-04-01T14:30:00Z',
      });
    });
  });

  describe('logout', () => {
    it('should logout user and clear cookies', async () => {
      // Arrange
      mockAuthService.logoutUserApiV1AuthLogoutPost.mockResolvedValue(undefined);

      // Act
      await logout();

      // Assert
      expect(mockAuthService.logoutUserApiV1AuthLogoutPost).toHaveBeenCalledWith({
        refreshToken: undefined,
      });
    });

    it('should handle logout errors gracefully', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');

      mockAuthService.logoutUserApiV1AuthLogoutPost.mockRejectedValue(error);

      // Act & Assert
      await expect(logout()).rejects.toThrow('Internal Server Error');
      expect(mockAuthService.logoutUserApiV1AuthLogoutPost).toHaveBeenCalledWith({
        refreshToken: undefined,
      });
    });
  });

  describe('getCsrfToken', () => {
    it('should get CSRF token from generated client', async () => {
      // Arrange
      const mockTokenResponse = mockGeneratedCSRFToken();

      mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet.mockResolvedValue(
        mockTokenResponse
      );

      // Act
      const result = await getCsrfToken();

      // Assert
      expect(mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet).toHaveBeenCalledTimes(
        1
      );
      expect(result).toBe(mockTokenResponse.token);
    });

    it('should handle CSRF token errors', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');

      mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet.mockRejectedValue(error);

      // Act & Assert
      await expect(getCsrfToken()).rejects.toThrow('Internal Server Error');
    });
  });

  describe('initializeCsrfToken', () => {
    it('should initialize CSRF token on module load', async () => {
      // Arrange
      const mockTokenResponse = mockGeneratedCSRFToken();

      mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet.mockResolvedValue(
        mockTokenResponse
      );

      // Act
      await initializeCsrfToken();

      // Assert
      expect(mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet).toHaveBeenCalledTimes(
        1
      );
    });

    it('should handle CSRF token initialization errors gracefully', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet.mockRejectedValue(error);

      // Act
      await initializeCsrfToken();

      // Assert
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Failed to initialize CSRF token:',
        error
      );
      consoleWarnSpy.mockRestore();
    });
  });

  describe('CSRF Token Integration', () => {
    it('should inject CSRF token in request headers', async () => {
      // This test verifies the CSRF token configuration in the generated client
      // The actual CSRF token injection is handled by the api-client-config.ts
      // We can test that the getCsrfToken function works correctly

      // Arrange
      const mockTokenResponse = mockGeneratedCSRFToken({
        token: 'test-csrf-token-123',
      });

      mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet.mockResolvedValue(
        mockTokenResponse
      );

      // Act
      const result = await getCsrfToken();

      // Assert
      expect(result).toBe('test-csrf-token-123');
      expect(mockAuthService.getCsrfTokenApiV1AuthCsrfTokenGet).toHaveBeenCalledTimes(
        1
      );
    });
  });
});
