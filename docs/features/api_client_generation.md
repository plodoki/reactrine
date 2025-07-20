# Type-Safe API Client Generation

To improve developer velocity and eliminate a common source of bugs, the Reactrine includes a system for automatically generating a type-safe TypeScript API client directly from your backend's OpenAPI specification.

## The Problem It Solves

Manually writing API fetching logic in the frontend is tedious and error-prone. When a backend API changes—for example, a new parameter is added to an endpoint or a field is renamed in a response—the frontend code can break silently at runtime.

This automated system solves that problem by creating a bridge between your FastAPI backend and your React frontend, ensuring that your API calls are always in sync with your backend's contract.

## How It Works

The system uses the `openapi-typescript-codegen` tool to introspect your running backend's OpenAPI schema (available at `/openapi.json`) and generate a full-featured TypeScript client.

This generated client includes:

- **TypeScript Interfaces:** For all your API request and response schemas (derived from your Pydantic models).
- **API Services:** Fully-typed functions for every endpoint in your API.
- **Compile-Time Safety:** If you try to call an endpoint with the wrong parameters, or if you try to access a property that doesn't exist on a response object, the TypeScript compiler will immediately flag it as an error.

## Generating the Client

To generate or update your API client, simply run the following command from the root of the project:

```bash
just api-client
```

**Prerequisite:** The backend development server must be running for this command to work, as it needs to fetch the live OpenAPI schema.

This command will execute the generation script and place the updated client in the `frontend/src/lib/api-client/` directory.

## Using the Generated Client

Once generated, you can import and use the client in your frontend components.

First, you need to configure the base URL for the API client. This should be done in a central location, like your main `App.tsx` or a dedicated API configuration file, and should use environment variables to ensure it works across different environments (development, staging, production).

```typescript
// frontend/src/lib/api-client-config.ts
import { OpenAPI } from "./api-client";

OpenAPI.BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
```

Then, you can import the services and call the API methods:

```typescript
// In one of your components or hooks
import { DefaultService } from "@/lib/api-client";
import { useEffect, useState } from "react";

function MyComponent() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    // This is a fully-typed API call!
    DefaultService.getSomeData()
      .then((response) => {
        setMessage(response.message);
      })
      .catch((error) => {
        console.error("API call failed:", error);
      });
  }, []);

  return <div>{message}</div>;
}
```

## Development Workflow

1.  Make changes to your FastAPI backend (e.g., add a new endpoint or modify a schema).
2.  Run `just api-client` to regenerate the frontend client.
3.  Update your frontend code to use the new or modified API endpoints. The TypeScript compiler will guide you, highlighting any code that needs to be changed.

This workflow creates a tight feedback loop between your backend and frontend, dramatically improving the reliability and maintainability of your application.
