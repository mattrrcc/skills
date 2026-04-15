#!/usr/bin/env python3
"""Converts Shopify locales/*.json to BigCommerce lang/*.json format."""

import json
import copy
import re


class LocaleConverter:
    """Convert Shopify locale files to BigCommerce language files.

    Both use nested JSON, but key naming conventions and some structures differ.
    Shopify: {{ 'key.path' | t }}
    BigCommerce: {{lang 'key.path'}}
    """

    # Key remapping for common Shopify-specific locale keys
    KEY_MAP = {
        'general.404': 'errors.404',
        'general.password_page': 'auth.password_page',
        'general.social': 'social',
        'general.search': 'search',
        'general.cart': 'cart',
        'general.pagination': 'pagination',
        'general.breadcrumbs': 'breadcrumbs',
        'customer.login': 'auth.login',
        'customer.register': 'auth.register',
        'customer.account': 'account',
        'customer.orders': 'account.orders',
        'customer.addresses': 'account.addresses',
        'customer.reset_password': 'auth.reset_password',
        'products.product': 'products',
        'products.general': 'products',
        'collections.general': 'categories',
        'collections.sorting': 'categories.sorting',
        'blogs.article': 'blog',
        'blogs.comments': 'blog.comments',
        'layout.cart': 'cart',
        'layout.customer': 'account',
        'sections.header': 'header',
        'sections.footer': 'footer',
        'sections.featured_product': 'products.featured',
        'sections.collection_template': 'categories',
    }

    def convert(self, shopify_locale: dict, locale_code: str = 'en') -> dict:
        """Convert a Shopify locale file to BigCommerce lang format.

        Args:
            shopify_locale: Parsed JSON from Shopify locale file
            locale_code: Language code (e.g., 'en', 'fr', 'es')

        Returns:
            BigCommerce-formatted language dictionary
        """
        bc_locale = {}

        # Flatten, remap keys, then rebuild nested structure
        flat = self._flatten(shopify_locale)
        remapped = {}

        for key, value in flat.items():
            new_key = self._remap_key(key)
            remapped[new_key] = self._convert_value(value)

        # Rebuild nested structure
        bc_locale = self._unflatten(remapped)

        return bc_locale

    def convert_all(self, locales: dict) -> dict:
        """Convert all locale files.

        Args:
            locales: {filename: parsed_json_content}

        Returns:
            {output_filename: converted_content}
        """
        result = {}
        for filename, content in locales.items():
            # Extract locale code: en.default.json -> en, fr.json -> fr
            code = filename.replace('.default', '').replace('.json', '')
            code = code.split('/')[-1]
            output_name = f'{code}.json'
            result[output_name] = self.convert(content, code)
        return result

    def _flatten(self, data: dict, prefix: str = '') -> dict:
        """Flatten nested dict to dot-separated keys."""
        flat = {}
        for key, value in data.items():
            full_key = f'{prefix}.{key}' if prefix else key
            if isinstance(value, dict):
                flat.update(self._flatten(value, full_key))
            else:
                flat[full_key] = value
        return flat

    def _unflatten(self, flat: dict) -> dict:
        """Rebuild nested dict from dot-separated keys."""
        nested = {}
        for key, value in sorted(flat.items()):
            parts = key.split('.')
            current = nested
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    # Conflict: existing leaf value, skip
                    break
                current = current[part]
            else:
                current[parts[-1]] = value
        return nested

    def _remap_key(self, key: str) -> str:
        """Remap Shopify-specific locale key paths to BigCommerce conventions."""
        # Check exact match first
        if key in self.KEY_MAP:
            return self.KEY_MAP[key]

        # Check prefix matches
        for shopify_prefix, bc_prefix in sorted(
            self.KEY_MAP.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if key.startswith(shopify_prefix + '.'):
                return bc_prefix + key[len(shopify_prefix):]

        return key

    def _convert_value(self, value) -> str:
        """Convert Liquid interpolation in locale values to Handlebars.

        Shopify: {{ count }} items
        BigCommerce: {{count}} items

        Shopify also uses %{count} for some interpolations.
        """
        if not isinstance(value, str):
            return value

        # Convert Liquid-style interpolations
        # {{ variable }} -> {{variable}}
        value = re.sub(r'\{\{\s*(\w+)\s*\}\}', r'{{\1}}', value)

        # Convert Ruby-style interpolations: %{variable} -> {{variable}}
        value = re.sub(r'%\{(\w+)\}', r'{{\1}}', value)

        return value
