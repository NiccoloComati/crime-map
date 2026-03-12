# Crime Map

## Startup

- Read [docs/CODEX_CONTEXT.md](/c:/Users/ncomati/Documents/GitHub/crime-map/docs/CODEX_CONTEXT.md) at the start of work for project background, architecture, deployment state, and user preferences.
- Read [docs/OPERATIONS.md](/c:/Users/ncomati/Documents/GitHub/crime-map/docs/OPERATIONS.md) before doing deployment, environment, or secret-related work.

## Source Of Truth

- The active product is the FastAPI + Next.js stack.
- Do not make product changes in `old/`.
- Keep one canonical implementation. Avoid duplicate code paths.

## Deployment

- Frontend is deployed from Vercel.
- Backend is deployed from Render.
- If deployment-related behavior changes, update [docs/OPERATIONS.md](/c:/Users/ncomati/Documents/GitHub/crime-map/docs/OPERATIONS.md).

## Context Maintenance

- When architecture, deployment workflow, taxonomy, or key UX behavior changes, update [docs/CODEX_CONTEXT.md](/c:/Users/ncomati/Documents/GitHub/crime-map/docs/CODEX_CONTEXT.md) in the same task.
- Keep that file concise and current. It is the persistent cross-chat project memory.

## Secrets

- Never commit secrets.
- Use environment variables or untracked local files only.
- If Render or Vercel credentials are needed, prefer `RENDER_API_KEY`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` from the local environment.
