# Varlock Decorators Reference

Use these decorators in your `.env.schema` file to enforce validation and behavior.

## Core Decorators

### `@sensitive`
Marks a variable as sensitive. Varlock will redact this value from logs and console output.
```properties
# @sensitive
OPENAI_API_KEY=
```

### `@required`

Ensures the variable must be present. The process will fail to start if it is missing.

```properties
# @required
DATABASE_URL=
```

### `@defaultSensitive`

(Root decorator) Sets the default sensitivity for all variables in the file.

```properties
# @defaultSensitive=true
# ---
KEY_1=...
```

## Type Validation

### `@type`

Enforces data types and formats.

**String validation:**

```properties
# @type=string(minLength=10, maxLength=100)
USERNAME=

# @type=string(format=email)
ADMIN_EMAIL=
```

**Numbers and Booleans:**

```properties
# @type=int(min=0, max=65535)
PORT=3000

# @type=boolean
DEBUG_MODE=false
```

**Enums:**
Restrict values to a specific set.

```properties
# @type=enum(development, staging, production)
NODE_ENV=development
```

## Dynamic Resolution

### `exec()`

Executes a command to fetch the value. Useful for integrating with 1Password, Vault, or AWS Secrets Manager.

```properties
STRIPE_KEY=exec('op read "op://prod/stripe/secret"')
```

### `fallback()`

Provides a fallback value if the primary is missing.

```properties
# Use PORT if set, otherwise default to 8080
app_port=fallback($PORT, 8080)
