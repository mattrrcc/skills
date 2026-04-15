# Shopify to BigCommerce Object Mapping Reference

## Product

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `product.title` | `product.title` | Direct |
| `product.description` | `product.description` | Direct |
| `product.price` | `product.price.without_tax.value` | Nested price object |
| `product.compare_at_price` | `product.price.rrp_without_tax.value` | |
| `product.available` | `product.purchasable` | |
| `product.handle` | `product.url` | BC uses full URL |
| `product.images` | `product.images` | Direct |
| `product.featured_image` | `product.main_image` | |
| `product.vendor` | `product.brand.name` | Nested |
| `product.type` | `product.category` | |
| `product.tags` | `product.tags` | Direct |
| `product.variants` | `product.options` | Different structure |
| `product.metafields` | `product.custom_fields` | Structure differs |

## Collection / Category

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `collection` | `category` | Different name |
| `collection.title` | `category.name` | |
| `collection.description` | `category.description` | |
| `collection.products` | `category.products` | |
| `collection.image` | `category.image` | |
| `collection.handle` | `category.url` | |

## Cart

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `cart.items` | `cart.items` | Direct |
| `cart.item_count` | `cart.quantity` | |
| `cart.total_price` | `cart.sub_total.without_tax.value` | |
| `item.title` | `this.name` | Inside each loop |
| `item.price` | `this.price.without_tax.value` | |
| `item.quantity` | `this.quantity` | |

## Store / Shop

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `shop.name` | `settings.store_name` | |
| `shop.url` | `settings.store_url` | |
| `shop.email` | `settings.store_email` | |
| `shop.currency` | `settings.currency` | |

## Customer

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `customer.first_name` | `customer.name` | BC combines names |
| `customer.email` | `customer.email` | |
| `customer.logged_in` | `customer` | Truthy check |
| `customer.orders` | `customer.orders` | |

## Blog / Article

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `blog.title` | `blog.name` | |
| `blog.articles` | `blog.posts` | |
| `article.title` | `blog.post.title` | |
| `article.content` | `blog.post.body` | |
| `article.author` | `blog.post.author` | |
| `article.created_at` | `blog.post.date_published` | |

## Navigation

| Shopify | BigCommerce | Notes |
|---------|-------------|-------|
| `linklists` | `navigation` | Fundamentally different |
| `linklist.links` | Navigation helper | Manual rebuild required |
| `link.title` | `this.name` | |
| `link.url` | `this.url` | |
| `link.links` (children) | `this.children` | |

## Settings

| Shopify | BigCommerce |
|---------|-------------|
| `settings.xxx` | `theme_settings.xxx` |
| `section.settings.xxx` | `theme_settings.xxx` |

## Layout / Template

| Shopify | BigCommerce |
|---------|-------------|
| `content_for_header` | `{{{head.meta_tags}}}` |
| `content_for_layout` | `{{{body}}}` |
| `page_title` | `{{{head.title}}}` |
| `canonical_url` | `{{{head.canonical_url}}}` |

## Loop Variables

| Shopify | BigCommerce |
|---------|-------------|
| `forloop.index` | `@index` |
| `forloop.first` | `@first` |
| `forloop.last` | `@last` |
| `forloop.length` | `@length` |
