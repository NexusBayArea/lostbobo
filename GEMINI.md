# SimHPC Development Guidelines

## Project Structure
We follow a strict monorepo structure to separate concerns and protect intellectual property.

- **`apps/`**: Deployable applications (e.g., React frontend, Next.js starter).
- **`services/`**: Backend microservices and workers.
- **`packages/`**: Shared libraries, SDKs, and internal tools.
- **`docs/`**: Centralized documentation.

## Best Practices
1. **Isolation**: Maintain clear boundaries between apps and services. Do not cross-import code directly between them; use shared `packages/` if necessary.
2. **Environment**: Store all secrets in `.env` (root or per-service). Never commit `.env` files.
3. **Documentation**: Keep `README.md` and `ARCHITECTURE.md` updated with any structural changes.
4. **Consistency**: Follow existing naming conventions (kebab-case for folders).
5. **Cleanliness**: Regularly clean up temporary files, build artifacts, and logs.

## Tooling
- **PowerShell**: Used for local environment management.
- **Docker Compose**: Used for local orchestration of services.
- **Git**: Primary version control. Do not stage/commit unless requested.
