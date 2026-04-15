#!/usr/bin/env python3
"""Maps Shopify Liquid objects/properties to BigCommerce Stencil equivalents."""

import re
from dataclasses import dataclass


@dataclass
class MappingResult:
    expression: str
    confident: bool
    note: str = ""


class ObjectMapper:
    """Rewrites Shopify object references to BigCommerce equivalents.

    Uses longest-prefix matching against a mapping table.
    """

    # Mapping table: shopify_path -> bigcommerce_path or (bc_path, note)
    MAPPINGS = {
        # Product
        "product.title": "product.title",
        "product.description": "product.description",
        "product.content": "product.description",
        "product.price": "product.price.without_tax.value",
        "product.compare_at_price": "product.price.rrp_without_tax.value",
        "product.price_min": "product.price.without_tax.value",
        "product.price_max": "product.price.price_range.max.without_tax.value",
        "product.price_varies": ("product.price.price_range", "Check if min != max"),
        "product.available": "product.purchasable",
        "product.handle": "product.url",
        "product.id": "product.id",
        "product.images": "product.images",
        "product.featured_image": "product.main_image",
        "product.image": "product.main_image",
        "product.images.first": "product.main_image",
        "product.url": "product.url",
        "product.vendor": "product.brand.name",
        "product.type": "product.category",
        "product.tags": "product.tags",
        "product.variants": "product.options",
        "product.options": "product.options",
        "product.selected_variant": "product.options[0]",
        "product.selected_or_first_available_variant": "product.options[0]",
        "product.first_available_variant": "product.options[0]",
        "product.has_only_default_variant": ("false", "BigCommerce always shows options"),
        "product.metafields": ("product.custom_fields", "Metafields map to custom fields"),
        "product.template_suffix": ("''", "No direct equivalent"),
        "product.published_at": "product.date_created",

        # Variant
        "variant.price": "this.price.without_tax.value",
        "variant.compare_at_price": "this.price.rrp_without_tax.value",
        "variant.title": "this.label",
        "variant.id": "this.id",
        "variant.available": "this.purchasable",
        "variant.sku": "this.sku",
        "variant.image": "this.image",
        "variant.url": "this.url",
        "variant.weight": "this.weight",
        "variant.inventory_quantity": ("this.stock", "Check inventory tracking"),

        # Collection -> Category
        "collection": "category",
        "collection.title": "category.name",
        "collection.description": "category.description",
        "collection.handle": "category.url",
        "collection.url": "category.url",
        "collection.id": "category.id",
        "collection.products": "category.products",
        "collection.all_products_count": "category.products.length",
        "collection.products_count": "category.products.length",
        "collection.image": "category.image",
        "collection.all_tags": ("category.faceted_search", "Tags differ from facets"),
        "collection.current_type": "category.name",
        "collection.sort_by": "category.sort_by",
        "collections": "categories",

        # Cart
        "cart": "cart",
        "cart.items": "cart.items",
        "cart.item_count": "cart.quantity",
        "cart.total_price": "cart.sub_total.without_tax.value",
        "cart.total_weight": ("cart.weight", "May not be available"),
        "cart.original_total_price": "cart.grand_total.without_tax.value",
        "cart.total_discount": "cart.discount.value",
        "cart.requires_shipping": ("true", "BigCommerce handles shipping differently"),
        "cart.note": ("cart.notes", "Cart notes API differs"),
        "cart.attributes": ("cart.custom_fields", "No direct equivalent"),

        # Cart item
        "item.product": "this",
        "item.title": "this.name",
        "item.product.title": "this.name",
        "item.price": "this.price.without_tax.value",
        "item.original_price": "this.price.without_tax.value",
        "item.final_price": "this.price.without_tax.value",
        "item.line_price": "this.total.without_tax.value",
        "item.original_line_price": "this.total.without_tax.value",
        "item.final_line_price": "this.total.without_tax.value",
        "item.quantity": "this.quantity",
        "item.url": "this.url",
        "item.image": "this.image",
        "item.variant": "this.options",
        "item.sku": "this.sku",
        "item.id": "this.id",
        "item.key": "this.id",
        "item.variant.title": "this.options[0].label",

        # Shop / Store
        "shop.name": "settings.store_name",
        "shop.url": "settings.store_url",
        "shop.secure_url": "settings.store_url",
        "shop.email": "settings.store_email",
        "shop.description": "settings.store_description",
        "shop.currency": "settings.currency",
        "shop.money_format": ("settings.money", "Format may differ"),
        "shop.money_with_currency_format": ("settings.money", "Format may differ"),
        "shop.domain": "settings.store_url",
        "shop.permanent_domain": "settings.store_url",
        "shop.locale": "locale_name",

        # Customer
        "customer": "customer",
        "customer.first_name": "customer.name",
        "customer.last_name": "customer.name",
        "customer.name": "customer.name",
        "customer.email": "customer.email",
        "customer.logged_in": "customer",
        "customer.id": "customer.id",
        "customer.orders": "customer.orders",
        "customer.orders_count": "customer.orders.length",
        "customer.total_spent": ("customer.store_credit", "Different concept"),
        "customer.tags": ("customer.customer_group", "Tags vs groups"),
        "customer.default_address": "customer.shipping_address",
        "customer.addresses": "customer.addresses",

        # Blog / Article
        "blog": "blog",
        "blog.title": "blog.name",
        "blog.url": "blog.url",
        "blog.id": "blog.id",
        "blog.articles": "blog.posts",
        "blog.articles_count": "blog.posts.length",
        "blog.all_tags": "blog.tags",
        "article": "blog.post",
        "article.title": "blog.post.title",
        "article.content": "blog.post.body",
        "article.excerpt": "blog.post.summary",
        "article.author": "blog.post.author",
        "article.created_at": "blog.post.date_published",
        "article.published_at": "blog.post.date_published",
        "article.image": "blog.post.thumbnail",
        "article.url": "blog.post.url",
        "article.id": "blog.post.id",
        "article.tags": "blog.post.tags",
        "article.comments": "blog.post.comments",
        "article.comments_count": "blog.post.comments.length",
        "article.comment": "blog.post.comment",
        "comment.author": "comment.author",
        "comment.content": "comment.text",
        "comment.email": "comment.email",

        # Page
        "page": "page",
        "page.title": "page.title",
        "page.content": "page.content",
        "page.url": "page.url",
        "page.handle": "page.url",
        "page.id": "page.id",
        "page.author": "page.author",
        "page.template_suffix": ("''", "No direct equivalent"),

        # Navigation
        "linklists": ("navigation", "Navigation structure is fundamentally different"),
        "linklist": ("navigation", "Use BigCommerce navigation helpers"),
        "link.title": "this.name",
        "link.url": "this.url",
        "link.active": "this.is_active",
        "link.child_active": "this.has_active_child",
        "link.links": "this.children",
        "link.type": ("'link'", "BigCommerce doesn't expose link types"),

        # Settings
        "settings": "theme_settings",

        # Pagination
        "paginate": "pagination",
        "paginate.pages": "pagination.total",
        "paginate.page_size": "pagination.per_page",
        "paginate.current_page": "pagination.current",
        "paginate.current_offset": ("pagination.offset", "May need calculation"),
        "paginate.next": "pagination.next",
        "paginate.previous": "pagination.previous",
        "paginate.parts": "pagination.pages",
        "paginate.items": "pagination.total_items",
        "part.title": "this.page",
        "part.url": "this.url",
        "part.is_link": "this.is_link",

        # Search
        "search": "search",
        "search.results": "search.product_results",
        "search.results_count": "search.product_results.length",
        "search.terms": "search.query",
        "search.performed": "search.query",
        "search.types": ("'product'", "BigCommerce primarily searches products"),

        # Request / Template
        "template": ("page_type", "BigCommerce uses page_type"),
        "template.name": ("page_type", "BigCommerce uses page_type"),
        "template.suffix": ("''", "No direct equivalent"),
        "request.path": "url.path",
        "request.host": "settings.store_url",
        "request.locale": "locale_name",
        "canonical_url": "head.canonical_url",
        "page_title": "head.title",
        "page_description": "head.meta_description",
        "content_for_header": "{{{head.meta_tags}}}",
        "content_for_layout": "{{{body}}}",

        # Image
        "image.src": "this.data",
        "image.alt": "this.alt",
        "image.width": "this.width",
        "image.height": "this.height",
        "image.aspect_ratio": ("this.width", "Calculate manually"),

        # Loop variables
        "forloop.index": "@index",
        "forloop.index0": "@index",
        "forloop.first": "@first",
        "forloop.last": "@last",
        "forloop.length": "@length",
        "forloop.rindex": ("@index", "Reverse index needs custom helper"),
        "forloop.rindex0": ("@index", "Reverse index needs custom helper"),

        # Global
        "current_page": "pagination.current",
        "current_tags": ("active_filters", "Different filtering mechanism"),
        "handle": "url",
        "now": ("now", "Use moment helper"),
        "tablerow": ("each", "No direct tablerow equivalent"),
    }

    def map_expression(self, expr: str) -> MappingResult:
        """Map a Shopify expression to BigCommerce."""
        expr = expr.strip()

        # Direct match
        if expr in self.MAPPINGS:
            return self._make_result(expr, self.MAPPINGS[expr])

        # Longest prefix match
        best_key = None
        for key in sorted(self.MAPPINGS.keys(), key=len, reverse=True):
            if expr.startswith(key + '.') or expr.startswith(key + '['):
                best_key = key
                break

        if best_key:
            mapping = self.MAPPINGS[best_key]
            if isinstance(mapping, tuple):
                bc_prefix = mapping[0]
                note = mapping[1]
            else:
                bc_prefix = mapping
                note = ""
            suffix = expr[len(best_key):]
            return MappingResult(bc_prefix + suffix, True, note)

        # Settings prefix
        if expr.startswith('settings.'):
            return MappingResult('theme_settings.' + expr[9:], True, "")

        # section.settings prefix (in sections)
        if expr.startswith('section.settings.'):
            return MappingResult('theme_settings.' + expr[17:], True,
                                 "Section settings mapped to theme settings")

        # block.settings prefix
        if expr.startswith('block.settings.'):
            return MappingResult('this.' + expr[15:], False,
                                 "Block settings need manual review")

        # Numbers, strings, booleans — pass through
        if re.match(r'^[\d.]+$', expr) or expr in ('true', 'false', 'nil', 'null', 'blank', 'empty'):
            return MappingResult(expr, True, "")

        # Quoted strings — pass through
        if (expr.startswith("'") and expr.endswith("'")) or \
           (expr.startswith('"') and expr.endswith('"')):
            return MappingResult(expr, True, "")

        # Unknown — pass through with note
        return MappingResult(expr, False, f"Unmapped expression: {expr}")

    def map_condition(self, condition: str) -> str:
        """Rewrite condition expressions, mapping object references."""
        # Tokenize condition: split on operators while preserving them
        tokens = re.split(r'(\s+(?:and|or|==|!=|>=|<=|>|<|contains)\s+)', condition)
        mapped = []
        for token in tokens:
            token_stripped = token.strip()
            if token_stripped in ('and', 'or', '==', '!=', '>=', '<=', '>', '<', 'contains'):
                mapped.append(token)
            elif token_stripped:
                result = self.map_expression(token_stripped)
                mapped.append(token.replace(token_stripped, result.expression))
            else:
                mapped.append(token)
        return ''.join(mapped)

    def _make_result(self, key: str, mapping) -> MappingResult:
        if isinstance(mapping, tuple):
            return MappingResult(mapping[0], True, mapping[1])
        return MappingResult(mapping, True, "")
