---
name: vercel
description: |
  Deploy and manage projects on Vercel using the Vercel CLI.
  Use when: "deploy to Vercel", "create a Vercel deployment", "check deployment status",
  "add environment variable", "set env var on Vercel", "manage Vercel domains",
  "link project to Vercel", "view deployment logs", "promote to production",
  "roll back deployment", "list Vercel projects", "Vercel preview deployment".
  Supports project linking, preview and production deployments, environment variable
  management, custom domains, deployment logs, and rollbacks.
  NOT for: managing other cloud providers (use their respective skills), building
  the project itself (do that before deploying).
license: Complete terms in LICENSE.txt
allowed-tools: Bash
---

# Vercel Deployment Skill

Deploy and manage projects on Vercel using the `vercel` CLI. This skill covers the full
deployment lifecycle: setup, deploy, environment configuration, domain management, and monitoring.

## Step 0 — Bootstrap

Before any other command, verify the CLI is available and the user is authenticated:

1. Check if `vercel` is installed:
   ```bash
   vercel --version
   ```
   If not found, install it:
   ```bash
   npm install -g vercel
   ```

2. Check authentication:
   ```bash
   vercel whoami
   ```
   If not authenticated, ask the user to run `vercel login` (interactive, opens a browser or sends an email) and confirm before continuing.

Skip both checks if `vercel whoami` already prints the account info.

## UX Rules

1. Be concise. Don't dump raw JSON into chat unless the user asks for it.
2. Always print the deployment URL when a deployment completes.
3. Confirm destructive actions (removing domains, deleting projects) before executing.
4. Don't batch-ask. Ask one clarifying question at a time only if genuinely missing critical info.
5. Use `--yes` / `--confirm` flags to skip interactive prompts in non-interactive contexts.

## Project Setup

### Link an existing project

Link the current directory to a Vercel project:
```bash
vercel link --yes
```

This creates a `.vercel/project.json` with the project and org IDs. If the directory is already linked, this is a no-op.

### Check link status

```bash
cat .vercel/project.json 2>/dev/null || echo "Not linked"
```

## Deployments

### Preview deployment (default)

Deploy the current directory as a preview:
```bash
vercel --yes
```
Returns a unique preview URL. Safe for testing — does not affect production traffic.

### Production deployment

Deploy to production (aliases the deployment to your production domain):
```bash
vercel --prod --yes
```

### Deploy a specific directory

```bash
vercel ./dist --yes
# or
vercel --yes --cwd ./my-app
```

### Check deployment status

List recent deployments for the linked project:
```bash
vercel list
```

Get details for a specific deployment:
```bash
vercel inspect <deployment-url-or-id>
```

### View deployment logs

Stream logs from the latest deployment:
```bash
vercel logs <deployment-url-or-id>
```

Follow logs in real-time:
```bash
vercel logs <deployment-url-or-id> --follow
```

### Promote a deployment to production

Promote an existing deployment without re-building:
```bash
vercel promote <deployment-url-or-id> --yes
```

### Roll back to a previous deployment

```bash
vercel rollback [deployment-url-or-id] --yes
```
If no ID is provided, Vercel rolls back to the previous production deployment.

### Cancel a running deployment

```bash
vercel cancel <deployment-url-or-id>
```

## Environment Variables

Environment variables are scoped to environments: `production`, `preview`, and `development`.

### List environment variables

```bash
vercel env ls
```

### Add an environment variable

Interactive (prompts for name, value, and environments):
```bash
vercel env add
```

Non-interactive (pipe the value):
```bash
echo "my-secret-value" | vercel env add MY_SECRET_KEY production
# Add to multiple environments:
echo "my-value" | vercel env add MY_KEY production preview development
```

### Pull environment variables to a local `.env` file

```bash
vercel env pull .env.local
```
This creates/overwrites `.env.local` with the development environment variables.

### Remove an environment variable

```bash
vercel env rm MY_KEY production --yes
```

## Domains

### List domains for the project

```bash
vercel domains ls
```

### Add a custom domain

```bash
vercel domains add example.com
```

### Remove a domain

```bash
vercel domains rm example.com --yes
```

### Inspect a domain (DNS, verification status)

```bash
vercel domains inspect example.com
```

## Project Management

### List all projects

```bash
vercel project ls
```

### Create a new project

```bash
vercel project add my-project-name
```

### Remove a project

```bash
vercel project rm my-project-name --yes
```

## Build Output Configuration

Vercel auto-detects frameworks. To override or customize, create/edit `vercel.json` in the project root.

Common `vercel.json` patterns:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm ci",
  "devCommand": "npm run dev",
  "framework": "nextjs"
}
```

For rewrites, redirects, and headers:
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://api.example.com/$1" }
  ],
  "redirects": [
    { "source": "/old-path", "destination": "/new-path", "permanent": true }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [{ "key": "X-Content-Type-Options", "value": "nosniff" }]
    }
  ]
}
```

## Common Workflows

### First-time deploy of a new project

```bash
# 1. Ensure CLI is installed and authenticated
vercel whoami

# 2. From the project root, deploy (links automatically on first run)
vercel --yes

# 3. Promote to production when ready
vercel --prod --yes
```

### CI/CD non-interactive deploy

Use a Vercel token (set `VERCEL_TOKEN` env var or pass `--token`):
```bash
vercel --prod --yes --token "$VERCEL_TOKEN"
```

### Pull and run locally with Vercel env vars

```bash
vercel env pull .env.local
# Now run your dev server; it will pick up .env.local
npm run dev
```

## Errors

- `Error: Not authenticated` → run `vercel login`.
- `Error: No project linked` → run `vercel link` first, or deploy from the project root.
- `Error: The provided token is not valid` → regenerate the token at vercel.com/account/tokens.
- `Build failed` → check `vercel logs <url>` for the full build output.
- `Domain already in use` → the domain is linked to another Vercel project or account.

## Reference

- Official docs: https://vercel.com/docs
- CLI reference: https://vercel.com/docs/cli
- `vercel.json` reference: https://vercel.com/docs/projects/project-configuration
