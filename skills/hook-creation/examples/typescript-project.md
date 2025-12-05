# TypeScript/Node.js Project Hook Example

Complete setup for a TypeScript or Node.js project with formatting, linting, compilation, and testing hooks.

## Project Structure

```
my-typescript-project/
├── .claude/
│   ├── settings.json              # Hook configuration
│   └── hooks/
│       ├── typescript-quality.sh  # PostToolUse: format and lint
│       └── typescript-build.sh    # Stop: compile and test
├── src/
├── tests/
├── package.json
├── tsconfig.json
├── biome.json  (or eslint config)
└── bun.lockb  (or package-lock.json)
```

## Configuration File

### `.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typescript-quality.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typescript-build.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## Hook Scripts

### `.claude/hooks/typescript-quality.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Read JSON input from Claude Code
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process TypeScript/JavaScript files
if [[ "$file_path" != *.ts && "$file_path" != *.tsx && "$file_path" != *.js && "$file_path" != *.jsx ]]; then
    exit 0
fi

echo "🔧 Processing TypeScript file: $(basename "$file_path")" >&2

# Check if we're in a Node.js project
if [[ ! -f "package.json" ]]; then
    echo "⚠️ No package.json found, skipping formatting" >&2
    exit 0
fi

# Prefer Biome over ESLint/Prettier
if command -v biome &> /dev/null; then
    echo "  Formatting with Biome..." >&2
    if biome check --write --unsafe "$file_path" 2>&1; then
        echo "  ✅ Formatted with Biome" >&2
    else
        echo "  ⚠️ Biome had issues" >&2
    fi

    echo "  Linting with Biome..." >&2
    if biome lint "$file_path" 2>&1; then
        echo "  ✅ Linted with Biome" >&2
    else
        echo "  ⚠️ Biome lint found issues" >&2
    fi

else
    # Fallback to Prettier
    if command -v prettier &> /dev/null; then
        echo "  Formatting with Prettier..." >&2
        if prettier --write "$file_path" 2>&1; then
            echo "  ✅ Formatted with Prettier" >&2
        else
            echo "  ⚠️ Prettier had issues" >&2
        fi
    fi

    # Fallback to ESLint
    if command -v eslint &> /dev/null && [[ -f ".eslintrc.*" ]] || [[ -f "eslint.config.js" ]]; then
        echo "  Linting with ESLint..." >&2
        if eslint "$file_path" 2>&1; then
            echo "  ✅ Linted with ESLint" >&2
        else
            echo "  ⚠️ ESLint found issues" >&2
        fi
    fi
fi

# Run related tests if they exist
if [[ -f "package.json" ]]; then
    # Look for test file
    dir=$(dirname "$file_path")
    base=$(basename "$file_path" | sed 's/\.[^.]*$//')

    test_files=(
        "$dir/${base}.test.ts"
        "$dir/${base}.test.tsx"
        "$dir/${base}.spec.ts"
        "$dir/${base}.spec.tsx"
        "$dir/test/${base}.test.ts"
        "tests/${base}.test.ts"
    )

    for test_file in "${test_files[@]}"; do
        if [[ -f "$test_file" ]]; then
            echo "  🧪 Running tests: $test_file" >&2

            # Use available test runner
            if command -v bun &> /dev/null; then
                if bun test "$test_file" 2>&1; then
                    echo "  ✅ Tests passed (bun)" >&2
                else
                    echo "  ❌ Tests failed (bun)" >&2
                fi
            elif command -v npm &> /dev/null; then
                if npm test -- "$test_file" 2>&1; then
                    echo "  ✅ Tests passed (npm)" >&2
                else
                    echo "  ❌ Tests failed (npm)" >&2
                fi
            fi
            break
        fi
    done
fi

exit 0
```

### `.claude/hooks/typescript-build.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running TypeScript checks..." >&2

# Check if TypeScript is configured
if [[ ! -f "tsconfig.json" ]]; then
    echo "⚠️ No tsconfig.json found, skipping TypeScript compilation" >&2
else
    # Try different TypeScript compilers
    if command -v bun &> /dev/null && bun --version | grep -q "1."; then
        echo "  Running bun tsc..." >&2
        if bun tsc --noEmit 2>&1; then
            echo "✅ TypeScript compilation passed (bun)" >&2
        else
            echo "❌ TypeScript compilation failed (bun)" >&2
            exit 2
        fi
    elif command -v tsc &> /dev/null; then
        echo "  Running tsc..." >&2
        if npx tsc --noEmit 2>&1; then
            echo "✅ TypeScript compilation passed" >&2
        else
            echo "❌ TypeScript compilation failed" >&2
            exit 2
        fi
    else
        echo "⚠️ TypeScript compiler not found" >&2
    fi
fi

# Run build if configured
if [[ -f "package.json" ]] && jq -e '.scripts.build' package.json > /dev/null 2>&1; then
    echo "🏗️ Running build..." >&2

    if command -v bun &> /dev/null && bun run build 2>&1; then
        echo "✅ Build succeeded (bun)" >&2
    elif command -v npm &> /dev/null && npm run build 2>&1; then
        echo "✅ Build succeeded (npm)" >&2
    else
        echo "❌ Build failed" >&2
        exit 2
    fi
fi

# Run test suite if configured
if [[ -f "package.json" ]]; then
    # Check for test scripts
    if jq -e '.scripts.test' package.json > /dev/null 2>&1; then
        echo "🧪 Running test suite..." >&2

        if command -v bun &> /dev/null; then
            if bun test 2>&1; then
                echo "✅ All tests passed (bun)" >&2
            else
                echo "❌ Tests failed (bun)" >&2
                exit 2
            fi
        elif command -v npm &> /dev/null; then
            if npm test 2>&1; then
                echo "✅ All tests passed (npm)" >&2
            else
                echo "❌ Tests failed (npm)" >&2
                exit 2
            fi
        fi
    fi
fi

exit 0
```

## Setup Instructions

1. **Create the directory structure**:
```bash
mkdir -p .claude/hooks
```

2. **Create the configuration**:
```bash
# Create settings.json
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typescript-quality.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typescript-build.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
EOF

# Create TypeScript quality hook
cat > .claude/hooks/typescript-quality.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" != *.ts && "$file_path" != *.tsx && "$file_path" != *.js && "$file_path" != *.jsx ]]; then
    exit 0
fi

echo "🔧 Processing TypeScript file: $(basename "$file_path")" >&2

if [[ ! -f "package.json" ]]; then
    echo "⚠️ No package.json found" >&2
    exit 0
fi

# Try Biome first
if command -v biome &> /dev/null; then
    biome check --write --unsafe "$file_path" 2>&1 && echo "  ✅ Formatted with Biome" >&2
    biome lint "$file_path" 2>&1 && echo "  ✅ Linted with Biome" >&2
else
    # Fallback to prettier/eslint
    command -v prettier &> /dev/null && prettier --write "$file_path" 2>&1 && echo "  ✅ Formatted with Prettier" >&2
    command -v eslint &> /dev/null && eslint "$file_path" 2>&1 && echo "  ✅ Linted with ESLint" >&2
fi

exit 0
EOF

# Create TypeScript build hook
cat > .claude/hooks/typescript-build.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running checks..." >&2

# TypeScript compilation
if [[ -f "tsconfig.json" ]]; then
    if command -v bun &> /dev/null; then
        bun tsc --noEmit 2>&1 && echo "✅ TypeScript passed" >&2 || { echo "❌ TypeScript failed" >&2; exit 2; }
    elif command -v tsc &> /dev/null; then
        npx tsc --noEmit 2>&1 && echo "✅ TypeScript passed" >&2 || { echo "❌ TypeScript failed" >&2; exit 2; }
    fi
fi

# Build if configured
if [[ -f "package.json" ]] && jq -e '.scripts.build' package.json > /dev/null 2>&1; then
    command -v bun &> /dev/null && bun run build 2>&1 && echo "✅ Build passed" >&2
    command -v npm &> /dev/null && npm run build 2>&1 && echo "✅ Build passed" >&2
fi

# Tests if configured
if [[ -f "package.json" ]] && jq -e '.scripts.test' package.json > /dev/null 2>&1; then
    command -v bun &> /dev/null && bun test 2>&1 && echo "✅ Tests passed" >&2
    command -v npm &> /dev/null && npm test 2>&1 && echo "✅ Tests passed" >&2
fi

exit 0
EOF

# Make executable
chmod +x .claude/hooks/*.sh
```

3. **Configure package.json** (example):
```json
{
  "name": "my-typescript-project",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "bun --watch src/index.ts",
    "build": "bun build src/index.ts --outdir dist",
    "test": "bun test",
    "lint": "biome check ."
  },
  "devDependencies": {
    "@biomejs/biome": "^1.8.0",
    "bun-types": "^1.1.0",
    "typescript": "^5.5.0"
  },
  "peerDependencies": {
    "typescript": "^5.0.0"
  }
}
```

4. **Configure Biome** (recommended over ESLint/Prettier):
```json
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/1.8.0/schema.json",
  "formatter": {
    "indentWidth": 2,
    "indentStyle": "space"
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "suspicious": {
        "noExplicitAny": "warn"
      }
    }
  },
  "javascript": {
    "formatter": {
      "semicolons": "asNeeded",
      "quoteStyle": "single"
    }
  },
  "typescript": {
    "formatter": {
      "semicolons": "asNeeded",
      "quoteStyle": "single"
    }
  }
}
```

5. **Configure tsconfig.json**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "strict": true,
    "skipLibCheck": true,
    "declaration": true,
    "outDir": "dist"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Usage

1. **Edit TypeScript/JavaScript files**:
   - Automatic formatting with Biome/Prettier
   - Automatic linting
   - Related tests run automatically

2. **When Claude finishes**:
   - TypeScript compilation check
   - Build process (if configured)
   - Full test suite

## Expected Output

### When editing a file:
```
🔧 Processing TypeScript file: main.ts
  Formatting with Biome...
  ✅ Formatted with Biome
  Linting with Biome...
  ✅ Linted with Biome
  🧪 Running tests: main.test.ts
  ✅ Tests passed (bun)
```

### When stopping:
```
🔍 Running TypeScript checks...
  Running bun tsc...
✅ TypeScript compilation passed (bun)
🏗️ Running build...
✅ Build succeeded (bun)
🧪 Running test suite...
✅ All tests passed (bun)
```

## Tool Preferences

The hooks automatically detect and use the best available tools:

1. **Runtime**: Bun preferred over npm
2. **Formatting/Linting**: Biome preferred over Prettier/ESLint
3. **TypeScript**: bun tsc preferred over npx tsc

## Troubleshooting

### Biome not formatting
- Check biome.json exists
- Verify file is in Biome's include/exclude patterns
- Run `biome check --write .` manually to debug

### TypeScript compilation fails
- Ensure tsconfig.json is valid
- Check for type errors
- Add `// @ts-ignore` or `// @ts-expect-error` for known issues

### Tests not running
- Verify test files match naming convention
- Check test script in package.json
- Ensure test framework is installed

### Hook doesn't execute
1. Check permissions: `chmod +x .claude/hooks/*.sh`
2. Verify JSON syntax: `jq . .claude/settings.json`
3. Restart Claude Code after changes