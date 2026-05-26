# oRPC Usage

oRPC is not used in the current frontend. This file exists to prevent future work from assuming the old template stack is present.

## Current State

- No oRPC dependency appears in `D:\g-code\frontend\package.json`.
- No oRPC client is initialized in `src/main.ts`.
- No generated oRPC query keys, React Query hooks, or RPC routers exist in the frontend source.
- The backend project described by `AGENTS.md` is FastAPI-based, so any RPC adoption must be an explicit architecture decision.

## If oRPC Is Introduced Later

Only add oRPC after confirming backend support and generated client strategy. Document:

- where the client is initialized
- how auth/session headers are attached
- how request/response types are generated
- how errors are mapped to Ant Design Vue messages or form errors
- how existing Pinia stores consume typed results

## Do Not

- Do not add React Query patterns to this Vue app.
- Do not name manual fetch wrappers as oRPC clients.
- Do not replace stable JSON API integration with oRPC without updating backend specs and frontend verification steps.

For current backend integration work, follow [api-integration.md](./api-integration.md) instead.
