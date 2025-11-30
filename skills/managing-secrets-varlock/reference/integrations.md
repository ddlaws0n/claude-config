# Integrations and Workflows

## Next.js Integration

Varlock has a native Next.js plugin to replace `@next/env`.

1. **Install Integration**:
   ```bash
   npm install @varlock/nextjs-integration
```

### 2. Update `next.config.js`

```javascript
const { varlockNextConfigPlugin } = require('@varlock/nextjs-integration/plugin');

const nextConfig = {
  // your config
};

module.exports = varlockNextConfigPlugin(nextConfig);
```

### 3. Usage
    Use `import { ENV } from 'varlock/env'` in your code. Varlock automatically handles `NEXT_PUBLIC_` inference if configured, or you can control it explicitly via schema.

## 3rd Party Secret Managers

Varlock works as a "glue" layer between your code and secret stores.

### 1Password

Prerequisite: Install `op` CLI and sign in.

```properties
# .env.schema
# @sensitive
AWS_SECRET_KEY=exec('op read "op://dev/aws/secret-key"')
```

### AWS Secrets Manager

Prerequisite: Install `aws` CLI and configure credentials.

```properties
# .env.schema
# @sensitive
DB_PASSWORD=exec('aws secretsmanager get-secret-value --secret-id prod/db --query SecretString --output text')
```
