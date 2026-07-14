"""
Inventory Management System - CLI Frontend
Author: Kosh
Repository: https://github.com/Ck-kosh/Python-REST-API-with-Flask--Inventory-summative-lab1.git

This CLI tool provides an interactive interface to manage inventory
through the Flask REST API.
"""

import requests
import json
import sys
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:5000"

class InventoryCLI:
    """Command Line Interface for Inventory Management System"""

    def __init__(self):
        self.api_url = API_BASE_URL
        self.session = requests.Session()

    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def print_success(self, message):
        """Print success message"""
        print(f"{message}")

    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")

    def print_info(self, message):
        """Print info message"""
        print(f"{message}")

    def print_item(self, item):
        """Pretty print an inventory item"""
        print(f"\n{'─' * 50}")
        print(f"   ID:          {item.get('id', 'N/A')}")
        print(f"    Name:        {item.get('product_name', 'N/A')}")
        print(f"  Brand:       {item.get('brand', 'N/A')}")
        print(f"  Category:    {item.get('category', 'N/A')}")
        print(f"  Description: {item.get('description', 'N/A')[:60]}...")
        print(f"  Stock:       {item.get('stock_level', 'N/A')} units")
        print(f"  Price:       ${item.get('price', 'N/A')}")
        print(f"   Barcode:     {item.get('barcode', 'N/A')}")
        print(f"   NutriScore:  {item.get('nutriscore_grade', 'N/A').upper()}")
        print(f"   Quantity:    {item.get('quantity', 'N/A')}")
        print(f"   Source:      {item.get('source', 'N/A')}")
        print(f"   Created:     {item.get('created_at', 'N/A')}")
        print(f"{'─' * 50}")

    # =========================================================================
    # MENU DISPLAY
    # =========================================================================

    def display_main_menu(self):
        """Display main menu options"""
        self.print_header("INVENTORY MANAGEMENT SYSTEM")
        print("""
    1.  View All Inventory Items
    2.  View Single Item (by ID)
    3.  Add New Item (Manual)
    4.  Add Item from OpenFoodFacts API
    5.   Update Item
    6.   Delete Item
    7.  Search OpenFoodFacts by Barcode
    8.  Search OpenFoodFacts by Name
    9.  View Inventory Statistics
    10. Seed Database with Mock Data
    11. Clear All Inventory
    0.  Exit
        """)

    # CRUD OPERATIONS

    def view_all_items(self):
        """Fetch and display all inventory items"""
        self.print_header("ALL INVENTORY ITEMS")

        try:
            response = self.session.get(f"{self.api_url}/inventory")
            data = response.json()

            if response.status_code == 200:
                items = data.get('data', [])
                count = data.get('count', 0)

                self.print_success(f"Found {count} item(s) in inventory")

                if items:
                    for item in items:
                        self.print_item(item)
                else:
                    self.print_info("Inventory is empty. Add some items first!")
            else:
                self.print_error(data.get('message', 'Failed to fetch items'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def view_single_item(self):
        """Fetch and display a single item by ID"""
        self.print_header("VIEW SINGLE ITEM")

        item_id = input("Enter item ID: ").strip()

        if not item_id:
            self.print_error("Item ID is required")
            return

        try:
            response = self.session.get(f"{self.api_url}/inventory/{item_id}")
            data = response.json()

            if response.status_code == 200:
                self.print_success("Item found!")
                self.print_item(data['data'])
            elif response.status_code == 404:
                self.print_error(f"Item with ID '{item_id}' not found")
            else:
                self.print_error(data.get('message', 'Failed to fetch item'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def add_item_manual(self):
        """Add a new inventory item manually"""
        self.print_header("ADD NEW ITEM (MANUAL)")

        print("Enter item details (press Enter to skip optional fields):\n")

        # Required fields
        product_name = input("Product Name *: ").strip()
        if not product_name:
            self.print_error("Product name is required")
            return

        try:
            stock_level = int(input("Stock Level *: ").strip())
        except ValueError:
            self.print_error("Stock level must be a number")
            return

        try:
            price = float(input("Price * ($): ").strip())
        except ValueError:
            self.print_error("Price must be a number")
            return

        # Optional fields
        brand = input("Brand: ").strip() or "Unknown"
        category = input("Category: ").strip() or "Uncategorized"
        description = input("Description: ").strip()
        barcode = input("Barcode: ").strip()

        item_data = {
            "product_name": product_name,
            "stock_level": stock_level,
            "price": price,
            "brand": brand,
            "category": category,
            "description": description,
            "barcode": barcode
        }

        try:
            response = self.session.post(
                f"{self.api_url}/inventory",
                json=item_data
            )
            data = response.json()

            if response.status_code == 201:
                self.print_success("Item added successfully!")
                self.print_item(data['data'])
            else:
                self.print_error(data.get('message', 'Failed to add item'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def add_item_from_api(self):
        """Add item using OpenFoodFacts API data"""
        self.print_header("ADD ITEM FROM OPENFOODFACTS API")

        print("This feature fetches product data from OpenFoodFacts using a barcode.\n")

        barcode = input("Enter product barcode: ").strip()

        if not barcode:
            self.print_error("Barcode is required")
            return

        # First, preview the product
        self.print_info("Fetching product details from OpenFoodFacts...")

        try:
            preview_response = self.session.get(f"{self.api_url}/api/search/barcode/{barcode}")
            preview_data = preview_response.json()

            if preview_response.status_code != 200:
                self.print_error(preview_data.get('message', 'Product not found'))
                return

            product = preview_data['data']
            print("\ Product Preview:")
            print(f"   Name: {product['product_name']}")
            print(f"   Brand: {product['brands']}")
            print(f"   Ingredients: {product['ingredients_text'][:80]}...")
            print(f"   NutriScore: {product['nutriscore_grade'].upper()}")

            confirm = input("\nAdd this product to inventory? (y/n): ").strip().lower()

            if confirm != 'y':
                self.print_info("Operation cancelled")
                return

            # Get stock and price from user
            try:
                stock_level = int(input("Enter stock level: ").strip())
            except ValueError:
                self.print_error("Stock level must be a number")
                return

            try:
                price = float(input("Enter price ($): ").strip())
            except ValueError:
                self.print_error("Price must be a number")
                return

            item_data = {
                "barcode": barcode,
                "stock_level": stock_level,
                "price": price
            }

            response = self.session.post(
                f"{self.api_url}/api/inventory/add-from-api",
                json=item_data
            )
            data = response.json()

            if response.status_code == 201:
                self.print_success("Item added from API successfully!")
                self.print_item(data['data'])
            else:
                self.print_error(data.get('message', 'Failed to add item'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def update_item(self):
        """Update an existing inventory item"""
        self.print_header("UPDATE ITEM")

        item_id = input("Enter item ID to update: ").strip()

        if not item_id:
            self.print_error("Item ID is required")
            return

        # First fetch the item
        try:
            get_response = self.session.get(f"{self.api_url}/inventory/{item_id}")

            if get_response.status_code != 200:
                self.print_error(f"Item with ID '{item_id}' not found")
                return

            current_item = get_response.json()['data']
            self.print_info("Current item details:")
            self.print_item(current_item)

            print("\nEnter new values (press Enter to keep current value):\n")

            updates = {}

            fields = [
                ("product_name", "Product Name"),
                ("brand", "Brand"),
                ("category", "Category"),
                ("description", "Description"),
                ("stock_level", "Stock Level"),
                ("price", "Price"),
                ("barcode", "Barcode")
            ]

            for field, label in fields:
                current_value = current_item.get(field, '')
                prompt = f"{label} [{current_value}]: "
                new_value = input(prompt).strip()

                if new_value:
                    if field in ['stock_level']:
                        try:
                            updates[field] = int(new_value)
                        except ValueError:
                            self.print_error(f"Invalid number for {label}")
                            continue
                    elif field in ['price']:
                        try:
                            updates[field] = float(new_value)
                        except ValueError:
                            self.print_error(f"Invalid number for {label}")
                            continue
                    else:
                        updates[field] = new_value

            if not updates:
                self.print_info("No changes made")
                return

            response = self.session.patch(
                f"{self.api_url}/inventory/{item_id}",
                json=updates
            )
            data = response.json()

            if response.status_code == 200:
                self.print_success("Item updated successfully!")
                self.print_item(data['data'])
            else:
                self.print_error(data.get('message', 'Failed to update item'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def delete_item(self):
        """Delete an inventory item"""
        self.print_header("DELETE ITEM")

        item_id = input("Enter item ID to delete: ").strip()

        if not item_id:
            self.print_error("Item ID is required")
            return

        # Confirm deletion
        try:
            get_response = self.session.get(f"{self.api_url}/inventory/{item_id}")

            if get_response.status_code != 200:
                self.print_error(f"Item with ID '{item_id}' not found")
                return

            item = get_response.json()['data']
            print(f"\n You are about to delete:")
            print(f"   Name: {item['product_name']}")
            print(f"   Brand: {item['brand']}")

            confirm = input("\nAre you sure? (yes/no): ").strip().lower()

            if confirm != 'yes':
                self.print_info("Deletion cancelled")
                return

            response = self.session.delete(f"{self.api_url}/inventory/{item_id}")
            data = response.json()

            if response.status_code == 200:
                self.print_success(f"Item '{item['product_name']}' deleted successfully")
            else:
                self.print_error(data.get('message', 'Failed to delete item'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    # EXTERNAL API OPERATIONS

    def search_by_barcode(self):
        """Search OpenFoodFacts by barcode"""
        self.print_header("SEARCH BY BARCODE")

        barcode = input("Enter barcode to search: ").strip()

        if not barcode:
            self.print_error("Barcode is required")
            return

        try:
            self.print_info("Searching OpenFoodFacts API...")
            response = self.session.get(f"{self.api_url}/api/search/barcode/{barcode}")
            data = response.json()

            if response.status_code == 200:
                product = data['data']
                self.print_success("Product found!")
                print(f"\n{'─' * 50}")
                print(f"    Name:        {product['product_name']}")
                print(f"   Brand:       {product['brands']}")
                print(f"   Ingredients: {product['ingredients_text'][:80]}...")
                print(f"   NutriScore:  {product['nutriscore_grade'].upper()}")
                print(f"   Categories:  {product['categories']}")
                print(f"   Quantity:    {product['quantity']}")
                print(f"   Source:      {product['source']}")
                print(f"{'─' * 50}")

                add = input("\nAdd this to inventory? (y/n): ").strip().lower()
                if add == 'y':
                    try:
                        stock = int(input("Stock level: "))
                        price = float(input("Price ($): "))

                        add_response = self.session.post(
                            f"{self.api_url}/api/inventory/add-from-api",
                            json={"barcode": barcode, "stock_level": stock, "price": price}
                        )

                        if add_response.status_code == 201:
                            self.print_success("Added to inventory!")
                        else:
                            self.print_error("Failed to add to inventory")
                    except ValueError:
                        self.print_error("Invalid number input")
            else:
                self.print_error(data.get('message', 'Product not found'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def search_by_name(self):
        """Search OpenFoodFacts by product name"""
        self.print_header("SEARCH BY PRODUCT NAME")

        name = input("Enter product name to search: ").strip()

        if not name:
            self.print_error("Product name is required")
            return

        try:
            self.print_info("Searching OpenFoodFacts API...")
            response = self.session.get(f"{self.api_url}/api/search/name/{name}")
            data = response.json()

            if response.status_code == 200:
                products = data.get('data', [])
                count = data.get('count', 0)

                self.print_success(f"Found {count} product(s)")

                for idx, product in enumerate(products, 1):
                    print(f"\n{'─' * 50}")
                    print(f"  #{idx}")
                    print(f"    Name:        {product['product_name']}")
                    print(f"   Brand:       {product['brands']}")
                    print(f"   Barcode:     {product['barcode']}")
                    print(f"   NutriScore:  {product['nutriscore_grade'].upper()}")
                    print(f"   Quantity:    {product['quantity']}")
                    print(f"{'─' * 50}")

                if products:
                    choice = input("\nEnter number to add to inventory (or Enter to skip): ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(products):
                        selected = products[int(choice) - 1]
                        try:
                            stock = int(input("Stock level: "))
                            price = float(input("Price ($): "))

                            add_response = self.session.post(
                                f"{self.api_url}/api/inventory/add-from-api",
                                json={
                                    "barcode": selected['barcode'],
                                    "stock_level": stock,
                                    "price": price
                                }
                            )

                            if add_response.status_code == 201:
                                self.print_success("Added to inventory!")
                            else:
                                self.print_error("Failed to add to inventory")
                        except ValueError:
                            self.print_error("Invalid number input")
            else:
                self.print_error(data.get('message', 'No products found'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    # =========================================================================
    # UTILITY OPERATIONS
    # =========================================================================

    def view_stats(self):
        """View inventory statistics"""
        self.print_header("INVENTORY STATISTICS")

        try:
            response = self.session.get(f"{self.api_url}/inventory/stats")
            data = response.json()

            if response.status_code == 200:
                stats = data['stats']
                print(f"\n  Total Items: {stats['total_items']}")
                print(f"   Total Value: ${stats['total_inventory_value']:.2f}")
                print(f"   Categories: {', '.join(stats['categories']) if stats['categories'] else 'None'}")

                low_stock = stats.get('low_stock_items', [])
                if low_stock:
                    print(f"\n    Low Stock Items (less than 10):")
                    for item in low_stock:
                        print(f"     • {item['product_name']} - {item['stock_level']} units")
                else:
                    print(f"\n   No low stock items")
            else:
                self.print_error(data.get('message', 'Failed to fetch stats'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def seed_database(self):
        """Seed database with mock data"""
        self.print_header("SEED DATABASE")

        confirm = input("This will add mock data to the inventory. Continue? (y/n): ").strip().lower()

        if confirm != 'y':
            self.print_info("Operation cancelled")
            return

        try:
            response = self.session.post(f"{self.api_url}/inventory/seed")
            data = response.json()

            if response.status_code == 201:
                self.print_success(data.get('message', 'Database seeded successfully'))
            else:
                self.print_error(data.get('message', 'Failed to seed database'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    def clear_inventory(self):
        """Clear all inventory items"""
        self.print_header("CLEAR INVENTORY")

        print("  WARNING: This will delete ALL inventory items!")
        confirm = input("Type 'DELETE ALL' to confirm: ").strip()

        if confirm != 'DELETE ALL':
            self.print_info("Operation cancelled")
            return

        try:
            response = self.session.delete(f"{self.api_url}/inventory/clear")
            data = response.json()

            if response.status_code == 200:
                self.print_success(data.get('message', 'Inventory cleared'))
            else:
                self.print_error(data.get('message', 'Failed to clear inventory'))

        except requests.ConnectionError:
            self.print_error("Cannot connect to API. Is the Flask server running?")
        except Exception as e:
            self.print_error(f"Error: {str(e)}")

    # MAIN LOOP

    def run(self):
        """Main CLI loop"""
        print("\n" + "=" * 30)
        print("   Welcome to Inventory Management System CLI")
        print("   Make sure Flask server is running on port 5000")
        print("=" * 30)

        while True:
            self.display_main_menu()
            choice = input("Enter your choice: ").strip()

            if choice == '1':
                self.view_all_items()
            elif choice == '2':
                self.view_single_item()
            elif choice == '3':
                self.add_item_manual()
            elif choice == '4':
                self.add_item_from_api()
            elif choice == '5':
                self.update_item()
            elif choice == '6':
                self.delete_item()
            elif choice == '7':
                self.search_by_barcode()
            elif choice == '8':
                self.search_by_name()
            elif choice == '9':
                self.view_stats()
            elif choice == '10':
                self.seed_database()
            elif choice == '11':
                self.clear_inventory()
            elif choice == '0':
                print("\n Goodbye! Thank you for using Inventory Management System.\n")
                sys.exit(0)
            else:
                self.print_error("Invalid choice. Please try again.")

            input("\nPress Enter to continue...")


def main():
    """Entry point for CLI"""
    cli = InventoryCLI()

    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n Goodbye! Thank you for using Inventory Management System.\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
