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

export interface LLMSettings {
  id: number;
  provider: string;
  openai_model: string;
  openrouter_model: string;
  bedrock_model: string;
  lmstudio_model: string;
}

export type CreateLLMSettings = Omit<LLMSettings, 'id'>;

// Role-related types for RBAC
export interface Role {
  name: string;
  description: string | null;
}

export interface User {
  id: number;
  email: string;
  auth_provider: string;
  is_active: boolean;
  role: Role | null;
  created_at: string;
  updated_at: string;
}

export interface UserList {
  users: User[];
  total: number;
  limit: number;
  offset: number;
}

export interface RoleList {
  roles: Role[];
  total: number;
}

export interface UserRoleUpdate {
  role_name: string;
}

export interface UserStatusUpdate {
  is_active: boolean;
}

export interface UserDeletionResponse {
  success: boolean;
  message: string;
  user_id: number;
}

// Task-related types
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

// Generic API error types to replace AxiosError
export interface ApiErrorResponse {
  status: number;
  statusText: string;
  data?: {
    detail?: string | Array<{ msg?: string; message?: string }>;
    error?: string;
  };
}

export class ApiError extends Error {
  public response: ApiErrorResponse;

  constructor(message: string, response: ApiErrorResponse) {
    super(message);
    this.name = 'ApiError';
    this.response = response;
  }

  static isApiError(error: unknown): error is ApiError {
    return error instanceof ApiError;
  }
}
