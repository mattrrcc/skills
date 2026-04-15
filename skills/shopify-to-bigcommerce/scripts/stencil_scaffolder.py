#!/usr/bin/env python3
"""Generates BigCommerce Stencil theme scaffolding files."""

import json
from pathlib import Path


class StencilScaffolder:
    """Create the required Stencil boilerplate for a BigCommerce theme.

    Generates:
    - package.json (with Stencil CLI dependencies)
    - .stencil (local dev config placeholder)
    - Required directory structure
    - Default page templates
    """

    DIRECTORIES = [
        'templates/layout',
        'templates/pages',
        'templates/pages/errors',
        'templates/components',
        'templates/components/common',
        'templates/components/sections',
        'templates/components/products',
        'templates/components/cart',
        'templates/components/account',
        'templates/components/blog',
        'assets/scss',
        'assets/scss/sections',
        'assets/js',
        'assets/js/sections',
        'assets/img',
        'assets/fonts',
        'lang',
    ]

    def scaffold(self, output_dir: Path, theme_name: str = 'converted-theme'):
        """Create the full directory structure and boilerplate files."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        # Create directories
        for d in self.DIRECTORIES:
            (output / d).mkdir(parents=True, exist_ok=True)

        # Generate package.json
        pkg = self._generate_package_json(theme_name)
        (output / 'package.json').write_text(json.dumps(pkg, indent=2))

        # Generate .stencil placeholder
        stencil_config = {
            'normalStoreUrl': 'https://your-store.mybigcommerce.com',
            'customLayouts': {
                'brand': {},
                'category': {},
                'page': {},
                'product': {}
            }
        }
        (output / '.stencil').write_text(json.dumps(stencil_config, indent=2))

        # Generate default page templates that may not come from Shopify
        self._generate_default_pages(output)

        # Generate default error pages
        self._generate_error_pages(output)

        # Generate common components
        self._generate_common_components(output)

    def _generate_package_json(self, theme_name: str) -> dict:
        return {
            'name': theme_name,
            'version': '1.0.0',
            'description': f'{theme_name} - Converted from Shopify',
            'main': 'assets/js/app.js',
            'author': '',
            'license': 'UNLICENSED',
            'dependencies': {
                '@bigcommerce/stencil-utils': '^6.0.0'
            },
            'devDependencies': {
                '@bigcommerce/stencil-cli': '^7.0.0'
            },
            'scripts': {
                'start': 'stencil start',
                'build': 'stencil bundle',
                'lint': 'echo \"No linting configured\"'
            }
        }

    def _generate_default_pages(self, output: Path):
        """Generate default page templates."""
        pages = {
            'home.html': '''\
{{!-- Home page --}}
{{#partial "page"}}
<div class="page-content" data-content-region="home_below_menu">
    {{{region name="home_below_menu"}}}
</div>

<div class="main-content">
    {{> components/sections/hero}}
    {{> components/sections/featured-products}}
    {{> components/sections/featured-categories}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'product.html': '''\
{{!-- Product page --}}
{{#partial "page"}}
<div class="product-page" itemscope itemtype="http://schema.org/Product">
    {{> components/products/product-view}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'category.html': '''\
{{!-- Category page --}}
{{#partial "page"}}
<div class="category-page">
    <h1 class="page-heading">{{category.name}}</h1>
    {{#if category.description}}
        <div class="category-description">{{{category.description}}}</div>
    {{/if}}
    <div class="product-grid">
        {{#each category.products}}
            {{> components/products/product-card}}
        {{/each}}
    </div>
    {{> components/common/pagination}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'cart.html': '''\
{{!-- Cart page --}}
{{#partial "page"}}
<div class="cart-page">
    <h1 class="page-heading">{{lang 'cart.title'}}</h1>
    {{> components/cart/cart-content}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'page.html': '''\
{{!-- Static page --}}
{{#partial "page"}}
<div class="static-page">
    <h1 class="page-heading">{{page.title}}</h1>
    <div class="page-content">{{{page.content}}}</div>
</div>
{{/partial}}
{{> layout/base}}
''',
            'blog.html': '''\
{{!-- Blog page --}}
{{#partial "page"}}
<div class="blog-page">
    <h1 class="page-heading">{{blog.name}}</h1>
    {{#each blog.posts}}
        {{> components/blog/post-card}}
    {{/each}}
    {{> components/common/pagination}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'blog-post.html': '''\
{{!-- Blog post page --}}
{{#partial "page"}}
<article class="blog-post">
    <h1 class="page-heading">{{blog.post.title}}</h1>
    <div class="post-meta">
        <span class="post-author">{{blog.post.author}}</span>
        <time class="post-date">{{blog.post.date_published}}</time>
    </div>
    <div class="post-content">{{{blog.post.body}}}</div>
</article>
{{/partial}}
{{> layout/base}}
''',
            'search.html': '''\
{{!-- Search results page --}}
{{#partial "page"}}
<div class="search-page">
    <h1 class="page-heading">{{lang 'search.title'}}</h1>
    {{#if search.query}}
        <p>{{lang 'search.results_for'}} "{{search.query}}"</p>
        {{#each search.product_results}}
            {{> components/products/product-card}}
        {{/each}}
        {{> components/common/pagination}}
    {{/if}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'brand.html': '''\
{{!-- Brand page --}}
{{#partial "page"}}
<div class="brand-page">
    <h1 class="page-heading">{{brand.name}}</h1>
    {{#each brand.products}}
        {{> components/products/product-card}}
    {{/each}}
    {{> components/common/pagination}}
</div>
{{/partial}}
{{> layout/base}}
''',
            'account/orders.html': '''\
{{!-- Account orders page --}}
{{#partial "page"}}
<div class="account-page">
    <h1 class="page-heading">{{lang 'account.orders.title'}}</h1>
    {{> components/account/order-list}}
</div>
{{/partial}}
{{> layout/base}}
''',
        }

        # Only write pages that don't already exist
        pages_dir = output / 'templates' / 'pages'
        for filename, content in pages.items():
            filepath = pages_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            if not filepath.exists():
                filepath.write_text(content)

    def _generate_error_pages(self, output: Path):
        """Generate error page templates."""
        errors_dir = output / 'templates' / 'pages' / 'errors'

        error_404 = '''\
{{!-- 404 Error page --}}
{{#partial "page"}}
<div class="error-page error-404">
    <h1 class="page-heading">{{lang 'errors.404.title'}}</h1>
    <p>{{lang 'errors.404.message'}}</p>
    <a href="/" class="button">{{lang 'errors.404.back_home'}}</a>
</div>
{{/partial}}
{{> layout/base}}
'''
        (errors_dir / '404.html').write_text(error_404)

    def _generate_common_components(self, output: Path):
        """Generate common component partials."""
        components_dir = output / 'templates' / 'components'

        # Pagination
        pagination = '''\
{{!-- Pagination component --}}
{{#if pagination}}
<nav class="pagination" aria-label="Pagination">
    {{#if pagination.previous}}
        <a href="{{pagination.previous.url}}" class="pagination-link pagination-prev">
            &laquo; {{lang 'pagination.previous'}}
        </a>
    {{/if}}
    {{#each pagination.pages}}
        {{#if this.is_current}}
            <span class="pagination-link pagination-current">{{this.page}}</span>
        {{else}}
            <a href="{{this.url}}" class="pagination-link">{{this.page}}</a>
        {{/if}}
    {{/each}}
    {{#if pagination.next}}
        <a href="{{pagination.next.url}}" class="pagination-link pagination-next">
            {{lang 'pagination.next'}} &raquo;
        </a>
    {{/if}}
</nav>
{{/if}}
'''
        (components_dir / 'common' / 'pagination.html').write_text(pagination)

        # Product card
        product_card = '''\
{{!-- Product card component --}}
<div class="product-card" data-product-id="{{id}}">
    <a href="{{url}}" class="product-card-link">
        {{#if main_image}}
            <img src="{{getImage main_image 'product_size'}}"
                 alt="{{main_image.alt}}"
                 class="product-card-image">
        {{/if}}
        <div class="product-card-body">
            <h3 class="product-card-title">{{name}}</h3>
            {{#if brand}}
                <span class="product-card-brand">{{brand.name}}</span>
            {{/if}}
            <div class="product-card-price">
                {{money price.without_tax.value}}
            </div>
        </div>
    </a>
</div>
'''
        (components_dir / 'products' / 'product-card.html').write_text(product_card)

        # Product view (detail page)
        product_view = '''\
{{!-- Product detail view --}}
<div class="product-view">
    <div class="product-gallery">
        {{#each product.images}}
            <img src="{{getImage this 'product_size'}}"
                 alt="{{this.alt}}"
                 class="product-image {{#if @first}}product-image--primary{{/if}}">
        {{/each}}
    </div>
    <div class="product-info">
        <h1 class="product-title">{{product.title}}</h1>
        {{#if product.brand}}
            <span class="product-brand">{{product.brand.name}}</span>
        {{/if}}
        <div class="product-price">
            {{money product.price.without_tax.value}}
            {{#if product.price.rrp_without_tax}}
                <span class="product-price--compare">
                    {{money product.price.rrp_without_tax.value}}
                </span>
            {{/if}}
        </div>
        <div class="product-description">{{{product.description}}}</div>

        <form action="/cart/add" method="post" enctype="multipart/form-data">
            <input type="hidden" name="action" value="add">
            <input type="hidden" name="product_id" value="{{product.id}}">

            {{#each product.options}}
                <div class="product-option">
                    <label>{{this.display_name}}</label>
                    <select name="attribute[{{this.id}}]">
                        {{#each this.values}}
                            <option value="{{this.id}}">{{this.label}}</option>
                        {{/each}}
                    </select>
                </div>
            {{/each}}

            <div class="product-quantity">
                <label>{{lang 'products.quantity'}}</label>
                <input type="number" name="qty[]" value="1" min="1">
            </div>

            <button type="submit" class="button button--primary">
                {{lang 'products.add_to_cart'}}
            </button>
        </form>
    </div>
</div>
'''
        (components_dir / 'products' / 'product-view.html').write_text(product_view)
