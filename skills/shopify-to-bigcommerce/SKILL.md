---
name: shopify-to-bigcommerce
description: >
  Convert Shopify Liquid themes to BigCommerce Stencil (Handlebars) themes and migrate
  store data. Use this skill when the user wants to migrate a Shopify theme to BigCommerce,
  convert Liquid templates to Handlebars, transform Shopify sections/snippets into Stencil
  components, port a Shopify storefront design to BigCommerce, or migrate Shopify store data
  (products, customers, orders) to BigCommerce format. Triggers on mentions of Shopify-to-BigCommerce
  migration, Liquid to Handlebars conversion, Stencil theme generation, or any e-commerce platform
  migration from Shopify to BigCommerce. Also use when users provide .liquid files and want them
  converted to BigCommerce format.
license: Apache-2.0
---

# Shopify to BigCommerce Migration

## Overview

This skill converts Shopify Liquid themes into BigCommerce Stencil (Handlebars) themes and helps migrate store data. It handles template conversion, object mapping, settings migration, asset porting, and data format transformation.

## Quick Start — Theme Conversion

```bash
python scripts/convert_theme.py /path/to/shopify/theme /path/to/output "my-theme"
```

This reads a Shopify theme directory and outputs a BigCommerce Stencil theme.

## Workflow

### Step 1: Gather Shopify Theme Files

Ask the user to provide their Shopify theme. They need at minimum:
- `layout/theme.liquid` — Main layout
- `templates/` — Page templates (index, product, collection, page, cart, blog, article, 404, search)
- `sections/` — Reusable sections
- `snippets/` — Code fragments
- `config/settings_schema.json` — Theme settings definitions
- `config/settings_data.json` — Theme settings values
- `assets/` — CSS, JS, images, fonts
- `locales/` — Translation files (optional)

If the user provides files individually, save them into a temporary directory matching the Shopify structure above.

### Step 2: Run Conversion

```bash
python scripts/convert_theme.py <shopify_dir> <output_dir> [theme_name]
```

### Step 3: Review Conversion Report

The tool generates `conversion-report.md` in the output directory. Read it and present key findings:
- Files successfully converted
- Items requiring manual review (with file paths and line numbers)
- Custom Handlebars helpers that need to be registered
- Unmapped Shopify objects/filters

### Step 4: Manual Fixes

Walk through each manual review item. Common fixes:
- **Navigation**: Shopify linklists must be rebuilt using BigCommerce's navigation system
- **Checkout**: BigCommerce has an optimized checkout — custom checkout Liquid won't transfer
- **App tags**: Shopify app-specific Liquid tags have no BigCommerce equivalent
- **Product variants**: Data model differences require manual mapping

### Step 5: Validate Output

The output should have this structure:
```
output/
├── templates/layout/base.html
├── templates/pages/*.html
├── templates/components/**/*.html
├── assets/scss/
├── assets/js/
├── assets/img/
├── config.json
├── schema.json
├── lang/*.json
└── package.json
```

## Data Migration

### Export from Shopify (via Matrixify)

Use Matrixify MCP tools to export all store data:
```
matrixify_export_create with entities: products, customers, orders,
custom_collections, smart_collections, pages, blog_posts, redirects, menus
```

### Convert to BigCommerce Format

```bash
python scripts/data_converter.py <matrixify_export.xlsx> <output_dir>
```

Generates BigCommerce-compatible CSV files for import via BigCommerce admin.

### Automated Sync (via Make.com)

Create a Make.com scenario using Shopify + BigCommerce modules:
- Shopify `searchProducts` → BigCommerce `createProduct`
- Shopify `searchCustomers` → BigCommerce `createCustomer`

## Reference Files

- `references/object-mapping.md` — Complete Shopify → BigCommerce object/property mapping
- `references/filter-mapping.md` — Liquid filter → Handlebars helper conversion table
- `references/cornerstone-reference.md` — BigCommerce Cornerstone theme structure guide

## Limitations

- Shopify checkout customization does not transfer (BigCommerce checkout is managed)
- Shopify app-specific Liquid tags have no equivalent
- Navigation must be manually rebuilt in BigCommerce admin
- Some Liquid filters require custom Handlebars helpers (generated automatically)
- OS 2.0 dynamic section ordering requires manual recreation in BigCommerce widgets
