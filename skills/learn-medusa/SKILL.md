---
name: learn-medusa
description: Expert guide for building and extending Medusa v2 headless commerce applications. Use when creating Medusa projects, building custom modules, workflows, API routes, admin extensions, subscribers, or scheduled jobs. Covers the full Medusa 2.x modular architecture.
---

# Medusa v2 Development Guide

Medusa is an open-source headless commerce platform built on Node.js. Medusa v2 introduced a modular architecture where commerce features are isolated, composable modules connected via links and orchestrated through workflows.

## Core Architecture

```
┌─────────────────────────────────────────────────┐
│                  HTTP Layer                      │
│          API Routes (Express-based)              │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│               Workflow Engine                    │
│     (steps + compensation + orchestration)       │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│                  Modules                         │
│  Product │ Order │ Customer │ Inventory │ ...    │
│  (each module owns its DB schema + service)      │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Module Links                        │
│     (connect records across module DBs)          │
└─────────────────────────────────────────────────┘
```

## Project Setup

### Create a new Medusa project
```bash
npx create-medusa-app@latest my-store
cd my-store
```

### Project structure
```
my-store/
├── src/
│   ├── api/           # Custom API routes
│   ├── modules/       # Custom modules
│   ├── workflows/     # Custom workflows
│   ├── subscribers/   # Event subscribers
│   ├── jobs/          # Scheduled jobs
│   ├── links/         # Module link definitions
│   └── admin/         # Admin UI extensions
├── medusa-config.ts   # Main configuration
└── package.json
```

### medusa-config.ts
```typescript
import { defineConfig } from "@medusajs/framework/config"

export default defineConfig({
  projectConfig: {
    databaseUrl: process.env.DATABASE_URL,
    redisUrl: process.env.REDIS_URL,
    http: {
      storeCors: process.env.STORE_CORS!,
      adminCors: process.env.ADMIN_CORS!,
      authCors: process.env.AUTH_CORS!,
      jwtSecret: process.env.JWT_SECRET || "supersecret",
      cookieSecret: process.env.COOKIE_SECRET || "supersecret",
    },
  },
  admin: {
    backendUrl: process.env.MEDUSA_BACKEND_URL,
  },
  modules: [
    // Built-in modules are included by default.
    // Add custom modules here:
    {
      resolve: "./src/modules/my-module",
      options: { apiKey: process.env.MY_API_KEY },
    },
  ],
})
```

---

## Modules

A module is a self-contained unit: data models, migrations, and a service. Modules can be Medusa's built-in modules or custom ones you build.

### Create a custom module

**src/modules/blog/index.ts** — module definition
```typescript
import BlogModuleService from "./service"
import { Module } from "@medusajs/framework/utils"

export const BLOG_MODULE = "blogModuleService"

export default Module(BLOG_MODULE, {
  service: BlogModuleService,
})
```

**src/modules/blog/models/post.ts** — data model
```typescript
import { model } from "@medusajs/framework/utils"

const Post = model.define("post", {
  id: model.id().primaryKey(),
  title: model.text(),
  handle: model.text().unique(),
  content: model.text().searchable(),
  published_at: model.dateTime().nullable(),
  author_id: model.text().nullable(),
})

export default Post
```

**src/modules/blog/service.ts** — service class
```typescript
import { MedusaService } from "@medusajs/framework/utils"
import Post from "./models/post"

class BlogModuleService extends MedusaService({ Post }) {
  // MedusaService auto-generates CRUD: createPosts, updatePosts,
  // retrievePost, listPosts, deletePost, etc.

  async publishPost(id: string) {
    return await this.updatePosts({ id }, { published_at: new Date() })
  }
}

export default BlogModuleService
```

**Run migrations after adding models:**
```bash
npx medusa db:generate blog  # generates migration files
npx medusa db:migrate         # applies migrations
```

### Model field types
```typescript
model.id()           // auto-generated ULID, use .primaryKey()
model.text()         // VARCHAR
model.number()       // INTEGER
model.float()        // FLOAT
model.boolean()      // BOOLEAN
model.dateTime()     // TIMESTAMP
model.json()         // JSONB
model.enum(["a","b"]) // ENUM
model.array()        // text[] array
model.bigNumber()    // NUMERIC for currency amounts

// Modifiers
.nullable()          // allows null
.optional()          // allows undefined (not set on create)
.unique()            // adds unique constraint
.searchable()        // marks for full-text search indexing
.index()             // adds DB index
.default(value)      // default value
```

### Model relationships
```typescript
// One-to-many: Post has many Comments
const Post = model.define("post", {
  id: model.id().primaryKey(),
  comments: model.hasMany(() => Comment),
})

const Comment = model.define("comment", {
  id: model.id().primaryKey(),
  post: model.belongsTo(() => Post, { mappedBy: "comments" }),
  post_id: model.text(),
})

// Many-to-many
const Product = model.define("product", {
  id: model.id().primaryKey(),
  tags: model.manyToMany(() => Tag, { mappedBy: "products" }),
})
```

---

## Workflows

Workflows compose steps into transactions. If a step fails, compensation functions undo previous steps automatically.

### Create a workflow

**src/workflows/create-post.ts**
```typescript
import {
  createWorkflow,
  createStep,
  StepResponse,
  WorkflowResponse,
} from "@medusajs/framework/workflows-sdk"
import { BLOG_MODULE } from "../modules/blog"
import BlogModuleService from "../modules/blog/service"

type CreatePostInput = {
  title: string
  content: string
}

// Step: validate and create the post
const createPostStep = createStep(
  "create-post-step",
  async (input: CreatePostInput, { container }) => {
    const blogService: BlogModuleService = container.resolve(BLOG_MODULE)

    const post = await blogService.createPosts({
      title: input.title,
      handle: input.title.toLowerCase().replace(/\s+/g, "-"),
      content: input.content,
    })

    // Second argument is the compensation payload
    return new StepResponse(post, post.id)
  },
  // Compensation: runs if a later step fails
  async (postId: string, { container }) => {
    const blogService: BlogModuleService = container.resolve(BLOG_MODULE)
    await blogService.deletePost(postId)
  }
)

// Workflow: compose steps
export const createPostWorkflow = createWorkflow(
  "create-post",
  (input: CreatePostInput) => {
    const post = createPostStep(input)
    return new WorkflowResponse(post)
  }
)
```

### Execute a workflow
```typescript
// In an API route or anywhere you have access to the container
const { result } = await createPostWorkflow(req.scope).run({
  input: { title: "Hello World", content: "First post!" },
})
```

### Workflow hooks (extend existing workflows)
```typescript
// src/workflows/hooks/product-created.ts
import { createProductsWorkflow } from "@medusajs/medusa/core-flows"

createProductsWorkflow.hooks.productsCreated(
  async ({ products }, { container }) => {
    // runs after products are created in the built-in workflow
    console.log("Products created:", products.map(p => p.id))
  }
)
```

---

## API Routes

Routes are Express handlers under `src/api/`. The folder path determines the URL path.

### Store route (public)
**src/api/store/posts/route.ts**
```typescript
import { MedusaRequest, MedusaResponse } from "@medusajs/framework/http"
import { BLOG_MODULE } from "../../../modules/blog"
import BlogModuleService from "../../../modules/blog/service"

export const GET = async (req: MedusaRequest, res: MedusaResponse) => {
  const blogService: BlogModuleService = req.scope.resolve(BLOG_MODULE)

  const [posts, count] = await blogService.listAndCountPosts(
    { published_at: { $ne: null } },
    { skip: 0, take: 20 }
  )

  res.json({ posts, count })
}

export const POST = async (req: MedusaRequest, res: MedusaResponse) => {
  // requires auth — use middleware to protect
  const { title, content } = req.body
  const blogService: BlogModuleService = req.scope.resolve(BLOG_MODULE)
  const post = await blogService.createPosts({ title, content })
  res.status(201).json({ post })
}
```

### Dynamic route segment
**src/api/store/posts/[id]/route.ts**
```typescript
import { MedusaRequest, MedusaResponse } from "@medusajs/framework/http"

export const GET = async (
  req: MedusaRequest,
  res: MedusaResponse
) => {
  const { id } = req.params
  // ...
}
```

### Middleware (auth, validation, CORS)
**src/api/middlewares.ts**
```typescript
import { defineMiddlewares, authenticate } from "@medusajs/framework/http"
import { z } from "zod"

export default defineMiddlewares({
  routes: [
    {
      // Protect all /admin/posts routes
      matcher: "/admin/posts*",
      middlewares: [authenticate("user", ["bearer", "session"])],
    },
    {
      // Validate POST body
      matcher: "/store/posts",
      method: "POST",
      bodyParser: {
        zod: z.object({
          title: z.string().min(1),
          content: z.string().min(1),
        }),
      },
    },
  ],
})
```

---

## Module Links

Links connect records from two different modules without coupling the modules together. The link owns the join table.

**src/links/blog-product.ts**
```typescript
import { defineLink } from "@medusajs/framework/utils"
import BlogModule from "../modules/blog"
import ProductModule from "@medusajs/medusa/product"

// Link a blog post to a Medusa product (one-to-one)
export default defineLink(BlogModule.linkable.post, ProductModule.linkable.product)
```

**Use links in routes/workflows:**
```typescript
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"

// In a route handler
const remoteLink = req.scope.resolve(ContainerRegistrationKeys.REMOTE_LINK)

// Create a link
await remoteLink.create({
  [BLOG_MODULE]: { post_id: post.id },
  [Modules.PRODUCT]: { product_id: product.id },
})

// Query linked data
const query = req.scope.resolve(ContainerRegistrationKeys.QUERY)
const { data: posts } = await query.graph({
  entity: "post",
  fields: ["id", "title", "product.*"],
  filters: { id: post.id },
})
```

---

## Subscribers (Event Handlers)

React to domain events emitted by modules.

**src/subscribers/post-published.ts**
```typescript
import type {
  SubscriberConfig,
  SubscriberArgs,
} from "@medusajs/framework"

export default async function postPublishedHandler({
  event: { data },
  container,
}: SubscriberArgs<{ id: string }>) {
  const { id } = data
  console.log(`Post ${id} was published — send notifications here`)
}

export const config: SubscriberConfig = {
  event: "post.published",   // custom event name from your service
}
```

**Emit events from a service:**
```typescript
import { MedusaService, EmitEvents } from "@medusajs/framework/utils"

class BlogModuleService extends MedusaService({ Post }) {
  @EmitEvents()
  async publishPost(id: string) {
    const post = await this.updatePosts({ id }, { published_at: new Date() })
    // Medusa auto-emits "post.updated"; for custom events use eventBusService
    return post
  }
}
```

---

## Scheduled Jobs

**src/jobs/sync-inventory.ts**
```typescript
import type { MedusaContainer } from "@medusajs/framework/types"

export default async function syncInventory(container: MedusaContainer) {
  // runs on the schedule below
  console.log("Syncing inventory...")
}

export const config = {
  name: "sync-inventory",
  schedule: "0 * * * *",   // every hour (cron syntax)
}
```

---

## Admin UI Extensions

Extend the Medusa admin dashboard with custom pages, widgets, and routes using React + Vite.

### Custom widget (embed in existing pages)
**src/admin/widgets/post-widget.tsx**
```tsx
import { defineWidgetConfig } from "@medusajs/admin-sdk"
import { Container, Heading, Text } from "@medusajs/ui"

const PostWidget = ({ data }: { data: { id: string } }) => {
  return (
    <Container>
      <Heading level="h2">Blog Posts</Heading>
      <Text>Linked posts for product {data.id}</Text>
    </Container>
  )
}

export const config = defineWidgetConfig({
  zone: "product.details.after",   // inject after product details
})

export default PostWidget
```

### Custom admin page
**src/admin/routes/blog/page.tsx**
```tsx
import { defineRouteConfig } from "@medusajs/admin-sdk"
import { PencilSquare } from "@medusajs/icons"
import { useQuery } from "@tanstack/react-query"
import { sdk } from "../../lib/sdk"

const BlogPage = () => {
  const { data } = useQuery({
    queryKey: ["posts"],
    queryFn: () => sdk.client.fetch("/admin/posts"),
  })

  return (
    <div>
      <h1>Blog Posts</h1>
      {data?.posts.map(post => <div key={post.id}>{post.title}</div>)}
    </div>
  )
}

export const config = defineRouteConfig({
  label: "Blog",
  icon: PencilSquare,
})

export default BlogPage
```

**src/admin/lib/sdk.ts** — Medusa admin SDK client
```typescript
import Medusa from "@medusajs/js-sdk"

export const sdk = new Medusa({
  baseUrl: import.meta.env.VITE_BACKEND_URL ?? "http://localhost:9000",
  auth: { type: "session" },
})
```

---

## Remote Query (Cross-Module Data Fetching)

The `query` service lets you fetch data across modules and their links in a single call.

```typescript
import { ContainerRegistrationKeys } from "@medusajs/framework/utils"

const query = container.resolve(ContainerRegistrationKeys.QUERY)

// Fetch products with their variants and inventory levels
const { data: products } = await query.graph({
  entity: "product",
  fields: [
    "id",
    "title",
    "variants.id",
    "variants.title",
    "variants.inventory_items.inventory.location_levels.*",
  ],
  filters: { id: ["prod_01", "prod_02"] },
  pagination: { skip: 0, take: 10 },
})
```

---

## Common Patterns

### Resolve built-in modules in routes/workflows
```typescript
import { Modules } from "@medusajs/framework/utils"

// In a route handler:
const productService = req.scope.resolve(Modules.PRODUCT)
const orderService = req.scope.resolve(Modules.ORDER)
const customerService = req.scope.resolve(Modules.CUSTOMER)
const cartService = req.scope.resolve(Modules.CART)
const inventoryService = req.scope.resolve(Modules.INVENTORY)
const pricingService = req.scope.resolve(Modules.PRICING)
const authService = req.scope.resolve(Modules.AUTH)
const notificationService = req.scope.resolve(Modules.NOTIFICATION)
```

### Use existing core-flows workflows
```typescript
import {
  createProductsWorkflow,
  createOrderWorkflow,
  createCartWorkflow,
  addToCartWorkflow,
  completeCartWorkflow,
  createCustomerWorkflow,
} from "@medusajs/medusa/core-flows"

const { result: products } = await createProductsWorkflow(req.scope).run({
  input: {
    products: [{
      title: "T-Shirt",
      variants: [{ title: "S", prices: [{ amount: 1000, currency_code: "usd" }] }],
    }],
  },
})
```

### Error handling
```typescript
import { MedusaError } from "@medusajs/framework/utils"

// Throw typed errors — Medusa maps these to HTTP status codes
throw new MedusaError(MedusaError.Types.NOT_FOUND, "Post not found")
throw new MedusaError(MedusaError.Types.INVALID_DATA, "Title is required")
throw new MedusaError(MedusaError.Types.NOT_ALLOWED, "Cannot delete published post")
// Types: NOT_FOUND (404), INVALID_DATA (400), NOT_ALLOWED (400),
//        UNAUTHORIZED (401), PAYMENT_AUTHORIZATION_ERROR (422),
//        DUPLICATE_ERROR (422), UNEXPECTED_STATE (500)
```

### Pagination helpers
```typescript
// List with offset pagination
const [items, count] = await service.listAndCountPosts(
  { published_at: { $ne: null } },          // filters
  { skip: offset, take: limit, order: { created_at: "DESC" } }  // options
)
res.json({ posts: items, count, offset, limit })
```

---

## Development Commands

```bash
npx medusa develop          # start dev server (port 9000)
npx medusa build            # production build
npx medusa db:generate      # generate migration for changed models
npx medusa db:migrate       # run pending migrations
npx medusa user -e admin@store.com -p password  # create admin user
npx medusa plugin:develop   # develop a Medusa plugin
```

## Environment Variables

```bash
DATABASE_URL=postgres://user:pass@localhost:5432/medusa
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret
COOKIE_SECRET=your-cookie-secret
STORE_CORS=http://localhost:8000
ADMIN_CORS=http://localhost:9000
AUTH_CORS=http://localhost:9000,http://localhost:8000
MEDUSA_BACKEND_URL=http://localhost:9000
```

## Live Documentation

For the latest Medusa documentation, use WebFetch on:
- Docs home: `https://docs.medusajs.com`
- Modules reference: `https://docs.medusajs.com/resources/references/modules`
- Workflows SDK: `https://docs.medusajs.com/resources/references/workflows`
- Core flows: `https://docs.medusajs.com/resources/references/core-flows`
- Admin extensions: `https://docs.medusajs.com/admin-widget-injection-zones`
