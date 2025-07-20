# Frontend

This is the frontend application built with React, TypeScript, and Vite.

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

## Generated API Client

The frontend now supports both handcrafted axios services and generated API client services for gradual migration.

### Using the Generated Client

To use the generated API client instead of the handcrafted services, set the environment variable:

```bash
# In your .env file or environment
VITE_USE_GENERATED_CLIENT=true
```

### Authentication Service Migration

The authentication service has been migrated to support both implementations:

#### Available Methods

- `checkRegistrationStatus()` / `checkRegistrationStatusWithGeneratedClient()`
- `register()` / `registerWithGeneratedClient()`
- `login()` / `loginWithGeneratedClient()`
- `loginWithGoogle()` / `loginWithGoogleWithGeneratedClient()`
- `getCurrentUser()` / `getCurrentUserWithGeneratedClient()`
- `logout()` / `logoutWithGeneratedClient()`
- `getCsrfToken()` / `getCsrfTokenWithGeneratedClient()`

#### Usage in Components

The `useAppStore` automatically uses the appropriate client based on the environment variable:

```typescript
import useAppStore from '@/stores/useAppStore';

const { login, register, logout, checkAuthStatus } = useAppStore();

// These methods will automatically use the generated client
// when VITE_USE_GENERATED_CLIENT=true
await login(email, password);
await register(email, password);
await logout();
```

#### Type Safety

The generated client provides full TypeScript type safety with generated types from the backend OpenAPI specification:

```typescript
import { User, RegistrationStatus } from '@/lib/api-client';

// Types are automatically generated and kept in sync with backend
const user: User = await authService.getCurrentUserWithGeneratedClient();
const status: RegistrationStatus =
  await authService.checkRegistrationStatusWithGeneratedClient();
```

### Benefits of Generated Client

1. **Type Safety**: Automatic TypeScript types from OpenAPI spec
2. **API Contract Validation**: Compile-time validation of API usage
3. **Consistency**: Consistent error handling and request/response patterns
4. **Maintenance**: Automatic updates when backend API changes
5. **Documentation**: Self-documenting API with generated types

### Migration Strategy

The migration follows a gradual approach:

1. **Parallel Implementation**: Both old and new methods exist side-by-side
2. **Environment Control**: Use `VITE_USE_GENERATED_CLIENT` to switch between implementations
3. **Backward Compatibility**: Existing code continues to work unchanged
4. **Gradual Rollout**: Test with generated client before full migration

### Next Steps

Other services (API Keys, LLM Settings, etc.) will be migrated following the same pattern established for authentication.

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run test` - Run tests
- `npm run lint` - Run linting
- `npm run typecheck` - Run type checking

## Architecture

The frontend uses:

- React 18 with functional components
- TypeScript for type safety
- Vite for fast development and building
- Zustand for state management
- React Query for server state
- Material-UI for components
- Generated API client for type-safe backend communication
