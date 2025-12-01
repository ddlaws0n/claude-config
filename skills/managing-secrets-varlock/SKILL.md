---
name: managing-secrets-varlock
description: Manage environment variables and secrets using Varlock. Use when configuring applications, securing API keys, migrating from dotenv, or setting up secrets management workflows.
---

# Managing Secrets with Varlock

This skill helps you secure application configuration using Varlock. It replaces insecure `.env` files with a typed, validated `.env.schema` system.

## Capabilities

- **Initialize Varlock**: Setup Varlock in existing projects
- **Schema Definition**: Create typed configuration schemas with validation
- **Secret Injection**: securely inject secrets from vaults (1Password, etc.)
- **Process Running**: Run applications with validated environments

## Instructions

### 1. Initialization

To add Varlock to a project, run:

```bash
npx varlock init
```

This creates a `.env.schema` file and configures `.gitignore`.

### 2. Defining Schema

Edit `.env.schema` to define variables. Use JSDoc-style decorators to enforce rules.

Example:

```properties
# @required @type=string(min=10)
API_KEY=

# @defaultSensitive=true
# @type=enum(development, production)
APP_ENV=development
```

### 3. Usage in Code

**Node.js/TypeScript**: Replace `process.env` with Varlock's typed object for runtime validation.

```typescript
import { ENV } from 'varlock/env';
console.log(ENV.API_KEY); // Typed and validated
```

**Python/Go/Other**: Use standard environment variable access methods (e.g., `os.environ`). Varlock injects these values when running the process.

### 4. Running Applications

Always run your application through the Varlock CLI to ensure validation and secret injection occur:

```bash
# Node
npx varlock run -- node app.js

# Python
npx varlock run -- python main.py
```

## Best Practices

- **Commit the Schema**: Always commit `.env.schema` to git.
- **Never Commit Secrets**: Secrets live in local `.env.local` (gitignored) or external vaults.
- **Use exec() for Vaults**: Fetch secrets dynamically rather than pasting them.

```properties
# @sensitive
DB_PASS=exec('op read "op://dev/db/password"')
```

## Reference

- **Decorators**: See `reference/decorators.md` for `@sensitive`, `@type`, etc.
- **Integrations**: See `reference/integrations.md` for Next.js and 3rd party tools.
- **Template**: View a starter schema in `templates/.env.schema`.

## Version History

- **v1.0.0 (2025-11-30)**: Initial release supporting Varlock CLI workflows
