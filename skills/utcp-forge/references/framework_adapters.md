# Framework Adapters Reference

## 1. FastAPI / Starlette
- **Route Decorators**: `@app.<method>`, `@router.<method>`
- **Path Parameters**: Extracted from decorator string (`/users/{user_id}`)
- **Body Schemas**: Annotated with Pydantic classes inheriting `BaseModel`
- **Authentication**: Injected via `Depends(get_current_user)` or `Header(...)`

## 2. Flask / Blueprint
- **Route Decorators**: `@app.route(path, methods=[...])` or `@blueprint.route(...)`
- **Path Parameters**: Formatted as `<converter:name>` (e.g. `<int:id>`)
- **Docstrings**: Parsed directly to synthesize descriptions when no OpenAPI exists

## 3. Express.js / Next.js
- **Route Definitions**: `app.get('/path', handler)`, `router.post('/path', ...)`
- **Path Parameters**: Formatted as `:param` (e.g. `/users/:id`), normalized to `{id}` for UTCP
