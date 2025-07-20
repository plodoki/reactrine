// Mock data factories for consistent test data
import type { User, Role } from '../types/api';

export interface RegistrationStatus {
  allowed: boolean;
  message?: string;
}

export interface CSRFToken {
  token: string;
}

// Import generated client types
import type {
  ApiKeyCreate as GeneratedApiKeyCreate,
  ApiKeyCreated as GeneratedApiKeyCreated,
  ApiKeyInfo as GeneratedApiKeyInfo,
  ApiKeyList as GeneratedApiKeyList,
  ApiKeyRevoked as GeneratedApiKeyRevoked,
  CSRFToken as GeneratedCSRFToken,
  LLMSettingsCreateSchema as GeneratedCreateLLMSettingsSchema,
  DatabaseTaskRequest as GeneratedDatabaseTaskRequest,
  ErrorTaskRequest as GeneratedErrorTaskRequest,
  HaikuRequest as GeneratedHaikuRequest,
  HaikuResponse as GeneratedHaikuResponse,
  LLMSettingsSchema as GeneratedLLMSettings,
  RegistrationStatus as GeneratedRegistrationStatus,
  TaskResponse as GeneratedTaskResponse,
  TaskResultResponse as GeneratedTaskResultResponse,
  TaskTriggerRequest as GeneratedTaskTriggerRequest,
  LLMSettingsUpdateSchema as GeneratedUpdateLLMSettingsSchema,
  User as GeneratedUser,
} from '@/lib/api-client';

export interface UserCreate {
  email: string;
  password: string;
  auth_provider: string;
}

export interface GoogleLoginRequest {
  credential: string;
}

export interface LoginFormData {
  username: string;
  password: string;
}

// Mock data factories
export const mockRole = (overrides?: Partial<Role>): Role => ({
  name: 'user',
  description: 'Standard user role',
  ...overrides,
});

export const mockUser = (overrides?: Partial<User>): User => ({
  id: 1,
  email: 'test@example.com',
  auth_provider: 'local',
  is_active: true,
  role: mockRole(),
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

export const mockAdminUser = (): User =>
  mockUser({
    id: 2,
    email: 'admin@example.com',
    role: mockRole({ name: 'admin', description: 'Administrator role' }),
  });

export const mockUserWithoutRole = (): User =>
  mockUser({
    id: 3,
    email: 'norole@example.com',
    role: null,
  });

export const mockRegistrationStatus = (
  overrides?: Partial<RegistrationStatus>
): RegistrationStatus => ({
  allowed: true,
  message: undefined,
  ...overrides,
});

export const mockCSRFToken = (overrides?: Partial<CSRFToken>): CSRFToken => ({
  token: 'test-csrf-token',
  ...overrides,
});

// Mock generated client responses
export const mockGeneratedUser = (
  overrides?: Partial<GeneratedUser>
): GeneratedUser => ({
  id: 1,
  email: 'test@example.com',
  auth_provider: 'local',
  is_active: true,
  role: mockRole(), // Generated user should also have role
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

export const mockGeneratedRegistrationStatus = (
  overrides?: Partial<GeneratedRegistrationStatus>
): GeneratedRegistrationStatus => ({
  allowed: true,
  message: null,
  ...overrides,
});

export const mockGeneratedCSRFToken = (
  overrides?: Partial<GeneratedCSRFToken>
): GeneratedCSRFToken => ({
  token: 'test-csrf-token',
  ...overrides,
});

export const mockUserCreate = (overrides?: Partial<UserCreate>): UserCreate => ({
  email: 'test@example.com',
  password: 'password123',
  auth_provider: 'email',
  ...overrides,
});

export const mockGoogleLoginRequest = (
  overrides?: Partial<GoogleLoginRequest>
): GoogleLoginRequest => ({
  credential: 'mock-google-credential',
  ...overrides,
});

export const mockLoginFormData = (
  overrides?: Partial<LoginFormData>
): LoginFormData => ({
  username: 'test@example.com',
  password: 'password123',
  ...overrides,
});

// Task-related types (matching the actual types from api.ts)
export type TaskStatus =
  | 'PENDING'
  | 'STARTED'
  | 'SUCCESS'
  | 'FAILURE'
  | 'RETRY'
  | 'REVOKED';

export interface TaskTriggerRequest {
  message: string;
}

export interface DatabaseTaskRequest {
  query: string;
}

export interface ErrorTaskRequest {
  should_fail?: boolean;
}

export interface TaskResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
}

export interface TaskResultResponse {
  task_id: string;
  status: TaskStatus;
  result?: Record<string, unknown> | null;
  error?: string | null;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface ActiveTasksResponse {
  [key: string]: unknown;
}

// Mock factories for task types
export const mockTaskTriggerRequest = (
  overrides?: Partial<TaskTriggerRequest>
): TaskTriggerRequest => ({
  message: 'Test task message',
  ...overrides,
});

export const mockDatabaseTaskRequest = (
  overrides?: Partial<DatabaseTaskRequest>
): DatabaseTaskRequest => ({
  query: 'SELECT * FROM test_table LIMIT 10',
  ...overrides,
});

export const mockErrorTaskRequest = (
  overrides?: Partial<ErrorTaskRequest>
): ErrorTaskRequest => ({
  should_fail: false,
  ...overrides,
});

export const mockTaskResponse = (overrides?: Partial<TaskResponse>): TaskResponse => ({
  task_id: 'test-task-123',
  status: 'PENDING',
  message: 'Task created successfully',
  ...overrides,
});

export const mockTaskResultResponse = (
  overrides?: Partial<TaskResultResponse>
): TaskResultResponse => ({
  task_id: 'test-task-123',
  status: 'SUCCESS',
  result: { data: 'test result' },
  error: null,
  created_at: '2024-01-01T10:00:00Z',
  completed_at: '2024-01-01T10:05:00Z',
  ...overrides,
});

export const mockActiveTasksResponse = (
  overrides?: Partial<ActiveTasksResponse>
): ActiveTasksResponse => ({
  'test-task-123': {
    name: 'test_task',
    state: 'PENDING',
    received: 1704096000.0,
  },
  'test-task-456': {
    name: 'database_task',
    state: 'SUCCESS',
    received: 1704096300.0,
  },
  ...overrides,
});

// Mock factories for generated client types
export const mockGeneratedTaskTriggerRequest = (
  overrides?: Partial<GeneratedTaskTriggerRequest>
): GeneratedTaskTriggerRequest => ({
  message: 'Test task message',
  ...overrides,
});

export const mockGeneratedDatabaseTaskRequest = (
  overrides?: Partial<GeneratedDatabaseTaskRequest>
): GeneratedDatabaseTaskRequest => ({
  query: 'SELECT * FROM test_table LIMIT 10',
  ...overrides,
});

export const mockGeneratedErrorTaskRequest = (
  overrides?: Partial<GeneratedErrorTaskRequest>
): GeneratedErrorTaskRequest => ({
  should_fail: false,
  ...overrides,
});

export const mockGeneratedTaskResponse = (
  overrides?: Partial<GeneratedTaskResponse>
): GeneratedTaskResponse => ({
  task_id: 'test-task-123',
  status: 'PENDING',
  message: 'Task created successfully',
  ...overrides,
});

export const mockGeneratedTaskResultResponse = (
  overrides?: Partial<GeneratedTaskResultResponse>
): GeneratedTaskResultResponse => ({
  task_id: 'test-task-123',
  status: 'SUCCESS',
  result: { data: 'test result' },
  error: null,
  created_at: '2024-01-01T10:00:00Z',
  completed_at: '2024-01-01T10:05:00Z',
  ...overrides,
});

// API Key types (matching the actual types from api.ts)
export interface ApiKey {
  id: number;
  label: string | null;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  is_active: boolean;
}

export interface CreateApiKeyRequest {
  label?: string;
  expires_in_days?: number;
}

export interface CreateApiKeyResponse {
  token: string;
  api_key: ApiKey;
}

// API Key mock factories
export const mockApiKey = (overrides?: Partial<ApiKey>): ApiKey => ({
  id: 1,
  label: 'Test API Key',
  created_at: '2024-01-01T00:00:00Z',
  expires_at: null,
  last_used_at: null,
  is_active: true,
  ...overrides,
});

export const mockCreateApiKeyRequest = (
  overrides?: Partial<CreateApiKeyRequest>
): CreateApiKeyRequest => ({
  label: 'Test API Key',
  expires_in_days: 30,
  ...overrides,
});

export const mockCreateApiKeyResponse = (
  overrides?: Partial<CreateApiKeyResponse>
): CreateApiKeyResponse => ({
  token: 'test-api-key-token',
  api_key: mockApiKey(),
  ...overrides,
});

// Generated client API Key mock factories
export const mockGeneratedApiKeyInfo = (
  overrides?: Partial<GeneratedApiKeyInfo>
): GeneratedApiKeyInfo => ({
  id: 1,
  label: 'Test API Key',
  created_at: '2024-01-01T00:00:00Z',
  expires_at: null,
  last_used_at: null,
  is_active: true,
  ...overrides,
});

export const mockGeneratedApiKeyCreate = (
  overrides?: Partial<GeneratedApiKeyCreate>
): GeneratedApiKeyCreate => ({
  label: 'Test API Key',
  expires_in_days: 30,
  ...overrides,
});

export const mockGeneratedApiKeyCreated = (
  overrides?: Partial<GeneratedApiKeyCreated>
): GeneratedApiKeyCreated => ({
  token: 'test-api-key-token',
  api_key: mockGeneratedApiKeyInfo(),
  ...overrides,
});

export const mockGeneratedApiKeyList = (
  overrides?: Partial<GeneratedApiKeyList>
): GeneratedApiKeyList => ({
  keys: [mockGeneratedApiKeyInfo()],
  total: 1,
  ...overrides,
});

export const mockGeneratedApiKeyRevoked = (
  overrides?: Partial<GeneratedApiKeyRevoked>
): GeneratedApiKeyRevoked => ({
  success: true,
  message: 'API key revoked successfully',
  ...overrides,
});

// LLM Settings types (matching the actual types from api.ts)
export interface LLMSettings {
  id: number;
  provider: string;
  openai_model: string;
  openrouter_model: string;
  bedrock_model: string;
  lmstudio_model: string;
}

export interface CreateLLMSettings {
  provider: string;
  openai_model: string;
  openrouter_model: string;
  bedrock_model: string;
  lmstudio_model: string;
}

// LLM Settings mock factories
export const mockLLMSettings = (overrides?: Partial<LLMSettings>): LLMSettings => ({
  id: 1,
  provider: 'openai',
  openai_model: 'gpt-4o-mini',
  openrouter_model: '',
  bedrock_model: '',
  lmstudio_model: '',
  ...overrides,
});

export const mockCreateLLMSettings = (
  overrides?: Partial<CreateLLMSettings>
): CreateLLMSettings => ({
  provider: 'openai',
  openai_model: 'gpt-4o-mini',
  openrouter_model: '',
  bedrock_model: '',
  lmstudio_model: '',
  ...overrides,
});

// Generated client LLM Settings mock factories
export const mockGeneratedLLMSettings = (
  overrides?: Partial<GeneratedLLMSettings>
): GeneratedLLMSettings => ({
  id: 1,
  provider: 'openai',
  openai_model: 'gpt-4o-mini',
  openrouter_model: null,
  bedrock_model: null,
  lmstudio_model: null,
  ...overrides,
});

export const mockGeneratedCreateLLMSettingsSchema = (
  overrides?: Partial<GeneratedCreateLLMSettingsSchema>
): GeneratedCreateLLMSettingsSchema => ({
  provider: 'openai',
  openai_model: 'gpt-4o-mini',
  openrouter_model: null,
  bedrock_model: null,
  lmstudio_model: null,
  ...overrides,
});

export const mockGeneratedUpdateLLMSettingsSchema = (
  overrides?: Partial<GeneratedUpdateLLMSettingsSchema>
): GeneratedUpdateLLMSettingsSchema => ({
  provider: 'openai',
  openai_model: 'gpt-4o-mini',
  openrouter_model: null,
  bedrock_model: null,
  lmstudio_model: null,
  ...overrides,
});

export const mockLMStudioModels = (): string[] => [
  'llama-3.2-3b-instruct',
  'llama-3.2-1b-instruct',
  'phi-3.5-mini-instruct',
];

// Haiku types (matching the actual types from api.ts)
export interface HaikuRequest {
  topic: string;
  style?: string;
  provider?: 'openai' | 'openrouter' | 'bedrock' | 'lmstudio' | null;
  model?: string | null;
}

export interface HaikuResponse {
  haiku: string;
  lines: string[];
  syllables: number[];
  model_used: string;
  provider_used: string;
}

// Haiku mock factories
export const mockHaikuRequest = (overrides?: Partial<HaikuRequest>): HaikuRequest => ({
  topic: 'nature',
  style: 'traditional',
  provider: null,
  model: null,
  ...overrides,
});

export const mockHaikuResponse = (
  overrides?: Partial<HaikuResponse>
): HaikuResponse => ({
  haiku: 'Cherry blossoms fall\nGently on the morning dew\nSpring awakens now',
  lines: ['Cherry blossoms fall', 'Gently on the morning dew', 'Spring awakens now'],
  syllables: [5, 7, 5],
  model_used: 'gpt-4o-mini',
  provider_used: 'openai',
  ...overrides,
});

// Generated client Haiku mock factories
export const mockGeneratedHaikuRequest = (
  overrides?: Partial<GeneratedHaikuRequest>
): GeneratedHaikuRequest => ({
  topic: 'nature',
  style: 'traditional',
  provider: null,
  model: null,
  ...overrides,
});

export const mockGeneratedHaikuResponse = (
  overrides?: Partial<GeneratedHaikuResponse>
): GeneratedHaikuResponse => ({
  haiku: 'Cherry blossoms fall\nGently on the morning dew\nSpring awakens now',
  lines: ['Cherry blossoms fall', 'Gently on the morning dew', 'Spring awakens now'],
  syllables: [5, 7, 5],
  model_used: 'gpt-4o-mini',
  provider_used: 'openai',
  ...overrides,
});
