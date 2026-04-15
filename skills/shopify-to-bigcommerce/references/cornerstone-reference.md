# BigCommerce Cornerstone Theme Reference

## Directory Structure

```
cornerstone/
├── assets/
│   ├── fonts/              # Custom fonts
│   ├── icons/              # SVG icons
│   ├── img/                # Theme images
│   ├── js/                 # JavaScript source
│   │   ├── app.js          # Main entry point
│   │   └── theme/          # Theme-specific JS modules
│   └── scss/               # SCSS source
│       ├── theme.scss      # Main stylesheet (import manifest)
│       ├── _variables.scss # SCSS variables from config.json
│       ├── components/     # Component-specific styles
│       ├── layouts/        # Layout styles
│       └── utilities/      # Utility classes
├── lang/                   # Language files
│   ├── en.json             # English (required)
│   └── [other].json        # Other languages
├── templates/
│   ├── layout/
│   │   └── base.html       # Main layout wrapper
│   ├── pages/              # Page-level templates
│   │   ├── home.html
│   │   ├── product.html
│   │   ├── category.html
│   │   ├── brand.html
│   │   ├── cart.html
│   │   ├── page.html
│   │   ├── blog.html
│   │   ├── blog-post.html
│   │   ├── search.html
│   │   ├── account/        # Account pages
│   │   └── errors/         # Error pages
│   └── components/         # Reusable partials
│       ├── common/         # Shared components
│       ├── products/       # Product components
│       ├── cart/            # Cart components
│       ├── account/        # Account components
│       └── blog/           # Blog components
├── config.json             # Theme configuration + settings values
├── schema.json             # Theme settings schema (admin UI)
├── package.json            # Node.js dependencies
└── .stencil                # Local dev config (not committed)
```

## base.html Structure

```handlebars
<!DOCTYPE html>
<html>
<head>
    <title>{{{head.title}}}</title>
    {{{head.meta_tags}}}
    {{{head.config}}}
    {{!-- Stylesheets --}}
    <link href="{{cdn 'assets/css/theme.css'}}" rel="stylesheet">
</head>
<body>
    {{> components/common/header}}

    <main class="body" role="main">
        {{{body}}}
    </main>

    {{> components/common/footer}}

    {{{footer.scripts}}}
    <script src="{{cdn 'assets/js/app.js'}}"></script>
</body>
</html>
```

## Page Template Pattern

```handlebars
{{!-- Page templates use the partial pattern --}}
{{#partial "page"}}
    <div class="page-content">
        {{!-- Page-specific content --}}
    </div>
{{/partial}}
{{> layout/base}}
```

## config.json Structure

```json
{
    "name": "Theme Name",
    "version": "1.0.0",
    "meta": {
        "price": 0,
        "features": ["fully_responsive", ...]
    },
    "css_compiler": "scss",
    "autoprefixer_cascade": true,
    "autoprefixer_browsers": ["> 1%", "last 2 versions"],
    "settings": {
        "color-primary": "#333333",
        "font-family": "Google_Karla_400"
    },
    "variations": [
        {
            "name": "Default",
            "id": "default",
            "meta": {
                "desktop_screenshot": "desktop.png",
                "mobile_screenshot": "mobile.png"
            },
            "settings": {}
        }
    ],
    "resources": {
        "cart": true,
        "bulk_discount_rates": true
    }
}
```

## schema.json Structure

```json
[
    {
        "name": "Colors",
        "settings": [
            {
                "type": "color",
                "label": "Primary Color",
                "id": "color-primary",
                "force_reload": true
            },
            {
                "type": "color",
                "label": "Secondary Color",
                "id": "color-secondary",
                "force_reload": true
            }
        ]
    },
    {
        "name": "Typography",
        "settings": [
            {
                "type": "font",
                "label": "Body Font",
                "id": "font-family"
            }
        ]
    }
]
```

## Built-in Handlebars Helpers

| Helper | Usage | Description |
|--------|-------|-------------|
| `{{getImage}}` | `{{getImage image "size"}}` | Image URL with size |
| `{{money}}` | `{{money price}}` | Currency formatting |
| `{{lang}}` | `{{lang 'key.path'}}` | Translation lookup |
| `{{json}}` | `{{json object}}` | JSON serialization |
| `{{cdn}}` | `{{cdn 'path'}}` | CDN asset URL |
| `{{region}}` | `{{{region name="x"}}}` | Widget region |
| `{{inject}}` | `{{inject "name" value}}` | Inject JS data |
| `{{jsContext}}` | `{{{jsContext}}}` | Output injected data |
| `{{stylesheet}}` | `{{{stylesheet 'path'}}}` | Include CSS |
| `{{getFonts}}` | `{{{getFonts}}}` | Font includes |
| `{{getImageSrcset}}` | `{{getImageSrcset image}}` | Responsive images |

## Stencil CLI Commands

```bash
# Initialize
stencil init

# Start dev server
stencil start

# Bundle for upload
stencil bundle

# Push to store
stencil push
```

## Important BigCommerce Concepts

- **Widgets/Regions**: Dynamic content areas managed via admin
- **Optimized Checkout**: BigCommerce's built-in checkout (not customizable via theme)
- **Price objects**: Always have `.without_tax` and `.with_tax` variants
- **Product options**: Different from Shopify variants — options are separate entities
- **Customer groups**: BigCommerce uses groups instead of tags for segmentation
- **Faceted search**: Category filtering through facets, not tags
