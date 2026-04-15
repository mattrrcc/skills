#!/usr/bin/env python3
"""Converts Matrixify/Shopify export data to BigCommerce CSV import format."""

import csv
import json
import sys
import os
from pathlib import Path


class DataConverter:
    """Convert Shopify product/customer/order data to BigCommerce CSV format.

    BigCommerce supports CSV import for:
    - Products (with variants, images)
    - Customers

    This converter reads Matrixify Excel exports (as CSV) or standard
    Shopify CSV exports and produces BigCommerce-compatible import files.
    """

    # Shopify -> BigCommerce product field mapping
    PRODUCT_MAP = {
        'Handle': 'Product URL',
        'Title': 'Product Name',
        'Body (HTML)': 'Product Description',
        'Vendor': 'Brand Name',
        'Product Category': 'Category',
        'Type': 'Product Type',
        'Tags': 'Search Keywords',
        'Published': 'Visible',
        'Variant SKU': 'Product Code/SKU',
        'Variant Grams': 'Weight',
        'Variant Price': 'Price',
        'Variant Compare At Price': 'Retail Price',
        'Variant Inventory Qty': 'Current Stock Level',
        'Variant Inventory Policy': 'Track Inventory',
        'Image Src': 'Product Image URL - 1',
        'Image Alt Text': 'Product Image Description - 1',
        'SEO Title': 'Page Title',
        'SEO Description': 'Meta Description',
        'Variant Barcode': 'UPC/EAN',
        'Status': 'Visible',
    }

    # Shopify -> BigCommerce customer field mapping
    CUSTOMER_MAP = {
        'First Name': 'First Name',
        'Last Name': 'Last Name',
        'Email': 'Email Address',
        'Phone': 'Phone',
        'Company': 'Company',
        'Address1': 'Address Line 1',
        'Address2': 'Address Line 2',
        'City': 'City',
        'Province': 'State/Province',
        'Province Code': 'State/Province Code',
        'Country': 'Country',
        'Country Code': 'Country Code',
        'Zip': 'Zip/Postcode',
        'Tags': 'Customer Group',
        'Note': 'Notes',
    }

    def convert_products(self, input_path: str, output_path: str) -> dict:
        """Convert Shopify product CSV to BigCommerce format.

        Returns a report dict.
        """
        report = {'total': 0, 'converted': 0, 'errors': []}

        rows = self._read_csv(input_path)
        if not rows:
            report['errors'].append(f'No data found in {input_path}')
            return report

        headers = list(rows[0].keys())
        bc_rows = []
        current_product = None
        image_index = 1

        for row in rows:
            report['total'] += 1
            bc_row = {}

            # Map fields
            for shopify_field, bc_field in self.PRODUCT_MAP.items():
                if shopify_field in row:
                    value = row[shopify_field]
                    bc_row[bc_field] = self._transform_product_value(
                        shopify_field, value
                    )

            # Handle product vs variant rows
            handle = row.get('Handle', '')
            if handle and handle != current_product:
                current_product = handle
                image_index = 1
            else:
                # Variant row — mark appropriately
                if not bc_row.get('Product Name'):
                    bc_row['Product Name'] = ''

            # Handle multiple images
            image_src = row.get('Image Src', '')
            if image_src:
                bc_row[f'Product Image URL - {image_index}'] = image_src
                alt = row.get('Image Alt Text', '')
                if alt:
                    bc_row[f'Product Image Description - {image_index}'] = alt
                image_index += 1

            # Handle variant options
            opt1_name = row.get('Option1 Name', '')
            opt1_value = row.get('Option1 Value', '')
            if opt1_name and opt1_value:
                bc_row[f'Option: {opt1_name}'] = opt1_value

            opt2_name = row.get('Option2 Name', '')
            opt2_value = row.get('Option2 Value', '')
            if opt2_name and opt2_value:
                bc_row[f'Option: {opt2_name}'] = opt2_value

            opt3_name = row.get('Option3 Name', '')
            opt3_value = row.get('Option3 Value', '')
            if opt3_name and opt3_value:
                bc_row[f'Option: {opt3_name}'] = opt3_value

            bc_rows.append(bc_row)
            report['converted'] += 1

        # Write output
        self._write_csv(output_path, bc_rows)
        return report

    def convert_customers(self, input_path: str, output_path: str) -> dict:
        """Convert Shopify customer CSV to BigCommerce format."""
        report = {'total': 0, 'converted': 0, 'errors': []}

        rows = self._read_csv(input_path)
        if not rows:
            report['errors'].append(f'No data found in {input_path}')
            return report

        bc_rows = []
        for row in rows:
            report['total'] += 1
            bc_row = {}

            for shopify_field, bc_field in self.CUSTOMER_MAP.items():
                if shopify_field in row:
                    bc_row[bc_field] = row[shopify_field]

            # Combine accepts_marketing
            if row.get('Accepts Marketing', '').lower() == 'yes':
                bc_row['Receives Newsletter'] = 'Yes'
            else:
                bc_row['Receives Newsletter'] = 'No'

            bc_rows.append(bc_row)
            report['converted'] += 1

        self._write_csv(output_path, bc_rows)
        return report

    def convert_all(self, input_dir: str, output_dir: str) -> dict:
        """Convert all available data files in a directory."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # Look for product files
        for name in ['products.csv', 'Products.csv', 'products_export.csv']:
            f = input_path / name
            if f.exists():
                out = output_path / 'bigcommerce_products.csv'
                results['products'] = self.convert_products(str(f), str(out))
                break

        # Look for customer files
        for name in ['customers.csv', 'Customers.csv', 'customers_export.csv']:
            f = input_path / name
            if f.exists():
                out = output_path / 'bigcommerce_customers.csv'
                results['customers'] = self.convert_customers(str(f), str(out))
                break

        return results

    def _transform_product_value(self, field: str, value: str) -> str:
        """Transform specific field values for BigCommerce compatibility."""
        if not value:
            return value

        if field == 'Published':
            return 'Y' if value.lower() in ('true', 'yes', 'web') else 'N'

        if field == 'Status':
            return 'Y' if value.lower() == 'active' else 'N'

        if field == 'Variant Inventory Policy':
            return 'by product' if value == 'deny' else 'by option'

        if field == 'Variant Grams':
            # Convert grams to kg for BigCommerce
            try:
                grams = float(value)
                return str(round(grams / 1000, 3))
            except ValueError:
                return value

        if field == 'Tags':
            # Shopify tags are comma-separated, BigCommerce uses same format
            return value

        return value

    def _read_csv(self, path: str) -> list:
        """Read CSV file and return list of dicts."""
        rows = []
        try:
            with open(path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except UnicodeDecodeError:
            with open(path, 'r', encoding='latin-1', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        return rows

    def _write_csv(self, path: str, rows: list):
        """Write list of dicts to CSV."""
        if not rows:
            return

        # Collect all unique headers
        headers = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    headers.append(key)
                    seen.add(key)

        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python data_converter.py <input_dir_or_file> <output_dir>')
        print()
        print('Converts Shopify/Matrixify export CSV files to BigCommerce import format.')
        print()
        print('Arguments:')
        print('  input_dir_or_file  Directory containing Shopify CSV exports,')
        print('                     or a single CSV file')
        print('  output_dir         Output directory for BigCommerce CSV files')
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    converter = DataConverter()

    if os.path.isfile(input_path):
        # Single file - auto-detect type
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        name = os.path.basename(input_path).lower()
        if 'customer' in name:
            out = str(output_path / 'bigcommerce_customers.csv')
            result = converter.convert_customers(input_path, out)
            print(f'Customers: {result["converted"]}/{result["total"]} converted')
        else:
            out = str(output_path / 'bigcommerce_products.csv')
            result = converter.convert_products(input_path, out)
            print(f'Products: {result["converted"]}/{result["total"]} converted')
    else:
        results = converter.convert_all(input_path, output_dir)
        for entity, result in results.items():
            print(f'{entity}: {result["converted"]}/{result["total"]} converted')
