#!/usr/bin/env python3
"""Migrates CSS, JS, images, and fonts from Shopify to BigCommerce structure."""

import re
import shutil
from pathlib import Path


class AssetMigrator:
    """Migrate assets from Shopify theme to BigCommerce Stencil structure.

    Shopify assets/ -> BigCommerce assets/{scss,js,img,fonts}/

    Key transformations:
    - CSS/CSS.liquid -> SCSS (with Liquid template tags converted to SCSS variables)
    - JS -> JS (with Shopify CDN references rewritten)
    - Images -> assets/img/
    - Fonts -> assets/fonts/
    """

    CSS_EXTENSIONS = {'.css', '.css.liquid', '.scss', '.scss.liquid'}
    JS_EXTENSIONS = {'.js', '.js.liquid'}
    IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.avif'}
    FONT_EXTENSIONS = {'.woff', '.woff2', '.ttf', '.otf', '.eot'}

    def __init__(self):
        self.warnings = []
        self.migrated_files = []
        self.scss_variables = set()

    def migrate(self, shopify_assets_dir: Path, output_dir: Path) -> dict:
        """Migrate all assets from Shopify to BigCommerce structure.

        Returns a report dict with migration details.
        """
        report = {
            'css_files': [],
            'js_files': [],
            'img_files': [],
            'font_files': [],
            'other_files': [],
            'scss_variables': [],
            'warnings': [],
        }

        if not shopify_assets_dir.exists():
            report['warnings'].append('No assets directory found')
            return report

        # Create output directories
        scss_dir = output_dir / 'assets' / 'scss'
        js_dir = output_dir / 'assets' / 'js'
        img_dir = output_dir / 'assets' / 'img'
        font_dir = output_dir / 'assets' / 'fonts'

        for d in [scss_dir, js_dir, img_dir, font_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Process each file
        for asset_file in sorted(shopify_assets_dir.iterdir()):
            if asset_file.is_dir():
                continue

            name = asset_file.name
            suffix = self._get_full_suffix(name)

            if suffix in self.CSS_EXTENSIONS or name.endswith('.css.liquid') or name.endswith('.scss.liquid'):
                self._migrate_css(asset_file, scss_dir, report)
            elif suffix in self.JS_EXTENSIONS or name.endswith('.js.liquid'):
                self._migrate_js(asset_file, js_dir, report)
            elif suffix in self.IMG_EXTENSIONS:
                self._migrate_image(asset_file, img_dir, report)
            elif suffix in self.FONT_EXTENSIONS:
                self._migrate_font(asset_file, font_dir, report)
            else:
                # Copy other files to img directory as fallback
                dest = img_dir / name
                shutil.copy2(asset_file, dest)
                report['other_files'].append(name)

        # Generate SCSS variables file
        if self.scss_variables:
            vars_content = self._generate_scss_variables()
            vars_file = scss_dir / '_variables.scss'
            vars_file.write_text(vars_content)
            report['scss_variables'] = sorted(self.scss_variables)

        # Generate main SCSS import file
        manifest = self._generate_scss_manifest(report['css_files'])
        manifest_file = scss_dir / 'theme.scss'
        manifest_file.write_text(manifest)

        report['warnings'] = self.warnings
        return report

    def _migrate_css(self, src: Path, dest_dir: Path, report: dict):
        """Convert CSS/Liquid-CSS to SCSS."""
        content = src.read_text(errors='replace')

        # Convert Liquid template tags to SCSS
        converted, new_vars = self._convert_liquid_in_css(content)

        self.scss_variables.update(new_vars)

        # Determine output filename
        name = src.name
        name = name.replace('.css.liquid', '.scss')
        name = name.replace('.scss.liquid', '.scss')
        if not name.endswith('.scss'):
            name = name.replace('.css', '.scss')

        # Prefix with underscore for SCSS partials (except main files)
        if not name.startswith('_') and name != 'theme.scss':
            name = '_' + name

        dest = dest_dir / name
        dest.write_text(converted)
        report['css_files'].append(name)

    def _migrate_js(self, src: Path, dest_dir: Path, report: dict):
        """Migrate JavaScript files."""
        content = src.read_text(errors='replace')

        # Rewrite Shopify-specific JS patterns
        converted = self._convert_js(content)

        name = src.name
        name = name.replace('.js.liquid', '.js')

        dest = dest_dir / name
        dest.write_text(converted)
        report['js_files'].append(name)

    def _migrate_image(self, src: Path, dest_dir: Path, report: dict):
        """Copy image files."""
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        report['img_files'].append(src.name)

    def _migrate_font(self, src: Path, dest_dir: Path, report: dict):
        """Copy font files."""
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        report['font_files'].append(src.name)

    def _convert_liquid_in_css(self, content: str) -> tuple:
        """Convert Liquid template tags in CSS to SCSS variables.

        {{ settings.color_primary }} -> $color_primary
        {% if settings.show_border %} -> kept as comment

        Returns (converted_css, set_of_scss_variable_names).
        """
        variables = set()

        # Replace {{ settings.xxx }} with SCSS variables
        def replace_settings(match):
            setting_name = match.group(1).strip()
            var_name = setting_name.replace('.', '-').replace('_', '-')
            variables.add(setting_name)
            return f'${var_name}'

        converted = re.sub(
            r'\{\{\s*settings\.(\w+)\s*\}\}',
            replace_settings,
            content
        )

        # Replace {{ settings.xxx | ... }} with SCSS variables
        def replace_settings_with_filter(match):
            setting_name = match.group(1).strip()
            var_name = setting_name.replace('.', '-').replace('_', '-')
            variables.add(setting_name)
            return f'${var_name}'

        converted = re.sub(
            r'\{\{\s*settings\.(\w+)\s*\|[^}]+\}\}',
            replace_settings_with_filter,
            converted
        )

        # Replace other {{ }} tags with comments
        converted = re.sub(
            r'\{\{([^}]+)\}\}',
            r'/* Liquid: {{\1}} */',
            converted
        )

        # Replace {% %} logic blocks with comments
        converted = re.sub(
            r'\{%[^%]*%\}',
            lambda m: f'/* Liquid: {m.group(0)} */',
            converted
        )

        # Rewrite asset URL references
        converted = re.sub(
            r"url\(['\"]?([^'\"()]+)\.(woff2?|ttf|otf|eot|svg|png|jpg|jpeg|gif|webp)['\"]?\)",
            r"url('../fonts/\1.\2')" if 'font' in content.lower() else r"url('../img/\1.\2')",
            converted
        )

        return converted, variables

    def _convert_js(self, content: str) -> str:
        """Convert Shopify-specific JS patterns."""
        # Replace Liquid tags in JS
        content = re.sub(
            r'\{\{\s*settings\.(\w+)\s*\}\}',
            r"window.theme_settings['\1']",
            content
        )

        # Replace other Liquid output tags
        content = re.sub(
            r'\{\{([^}]+)\}\}',
            r"/* Liquid: {{\1}} */",
            content
        )

        # Replace Liquid logic tags
        content = re.sub(
            r'\{%[^%]*%\}',
            lambda m: f'/* Liquid: {m.group(0)} */',
            content
        )

        # Replace Shopify AJAX API paths
        content = content.replace('/cart.js', '/api/storefront/cart')
        content = content.replace('/cart/add.js', '/api/storefront/cart')
        content = content.replace('/cart/update.js', '/api/storefront/cart')
        content = content.replace('/cart/change.js', '/api/storefront/cart')
        content = content.replace('/search/suggest.json', '/api/storefront/search')

        return content

    def _generate_scss_variables(self) -> str:
        """Generate SCSS variables file from extracted Liquid settings."""
        lines = [
            '// Auto-generated SCSS variables from Shopify theme settings',
            '// Map these to your BigCommerce theme_settings in config.json',
            '',
        ]
        for var in sorted(self.scss_variables):
            var_name = var.replace('.', '-').replace('_', '-')
            lines.append(f'${var_name}: inherit !default;')
        return '\n'.join(lines)

    def _generate_scss_manifest(self, css_files: list) -> str:
        """Generate main SCSS file that imports all converted stylesheets."""
        lines = [
            '// Main theme stylesheet',
            '// Auto-generated during Shopify to BigCommerce conversion',
            '',
            '// Variables',
            "@import 'variables';",
            '',
            '// Converted Shopify stylesheets',
        ]
        for name in sorted(css_files):
            if name == 'theme.scss' or name == '_variables.scss':
                continue
            import_name = name.replace('.scss', '').lstrip('_')
            lines.append(f"@import '{import_name}';")

        return '\n'.join(lines)

    def _get_full_suffix(self, filename: str) -> str:
        """Get the full suffix including compound extensions like .css.liquid."""
        if filename.endswith('.css.liquid'):
            return '.css.liquid'
        if filename.endswith('.scss.liquid'):
            return '.scss.liquid'
        if filename.endswith('.js.liquid'):
            return '.js.liquid'
        return Path(filename).suffix.lower()
