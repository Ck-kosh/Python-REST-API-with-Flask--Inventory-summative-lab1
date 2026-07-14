"""
Inventory Management System - Flask REST API
Author: Kosh
Repository: https://github.com/Ck-kosh/Python-REST-API-with-Flask--Inventory-summative-lab1.git
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import uuid
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory database (mock storage)
inventory_db = []

# OpenFoodFacts API Configuration
OPENFOODFACTS_API = "https://world.openfoodfacts.org/api/v0"

def generate_id():
    """Generate unique ID for inventory items"""
    return str(uuid.uuid4())

def find_item_by_id(item_id):
    """Find an item in the inventory by ID"""
    for item in inventory_db:
        if item["id"] == item_id:
            return item
    return None

def find_item_index(item_id):
    """Find index of item in inventory array"""
    for index, item in enumerate(inventory_db):
        if item["id"] == item_id:
            return index
    return -1

# EXTERNAL API INTEGRATION - OpenFoodFacts

def fetch_product_by_barcode(barcode):
    """
    Fetch product details from OpenFoodFacts API using barcode
    Returns product data or None if not found
    """
    try:
        url = f"{OPENFOODFACTS_API}/product/{barcode}.json"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                return {
                    "product_name": product.get("product_name", "Unknown Product"),
                    "brands": product.get("brands", "Unknown Brand"),
                    "ingredients_text": product.get("ingredients_text", "Not available"),
                    "nutriscore_grade": product.get("nutriscore_grade", "N/A"),
                    "categories": product.get("categories", "N/A"),
                    "image_url": product.get("image_url", ""),
                    "quantity": product.get("quantity", "N/A"),
                    "source": "OpenFoodFacts"
                }
        return None
    except Exception as e:
        print(f"Error fetching product by barcode: {e}")
        return None

def fetch_product_by_name(product_name):
    """
    Search for products by name using OpenFoodFacts API
    Returns list of matching products or empty list
    """
    try:
        url = f"{OPENFOODFACTS_API}/search"
        params = {
            "search_terms": product_name,
            "page_size": 5,
            "json": 1
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            results = []
            for product in products:
                results.append({
                    "product_name": product.get("product_name", "Unknown"),
                    "brands": product.get("brands", "Unknown"),
                    "barcode": product.get("code", "N/A"),
                    "ingredients_text": product.get("ingredients_text", "Not available"),
                    "nutriscore_grade": product.get("nutriscore_grade", "N/A"),
                    "categories": product.get("categories", "N/A"),
                    "image_url": product.get("image_url", ""),
                    "quantity": product.get("quantity", "N/A"),
                    "source": "OpenFoodFacts"
                })
            return results
        return []
    except Exception as e:
        print(f"Error fetching product by name: {e}")
        return []

# REST API ROUTES - CRUD OPERATIONS

@app.route('/')
def home():
    """Root endpoint - API information or a browser-friendly landing page"""
    if request.accept_mimetypes.best == 'text/html':
        html = """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Inventory Management System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f7f9fc; color: #1f2937; }
                .container { max-width: 900px; margin: 40px auto; background: white; padding: 32px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
                h1 { color: #2563eb; }
                code { background: #eef2ff; padding: 2px 6px; border-radius: 4px; }
                ul { line-height: 1.7; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Inventory Management System</h1>
                <p>This application provides a Flask REST API for managing inventory items and enriching them with OpenFoodFacts data.</p>
                <h2>Available endpoints</h2>
                <ul>
                    <li><code>GET /inventory</code> - view all inventory items</li>
                    <li><code>GET /inventory/&lt;id&gt;</code> - view one item</li>
                    <li><code>POST /inventory</code> - add an item</li>
                    <li><code>PATCH /inventory/&lt;id&gt;</code> - update an item</li>
                    <li><code>DELETE /inventory/&lt;id&gt;</code> - delete an item</li>
                    <li><code>GET /api/search/barcode/&lt;barcode&gt;</code> - search by barcode</li>
                    <li><code>GET /api/search/name/&lt;name&gt;</code> - search by name</li>
                </ul>
                <p>Use the API endpoints directly for data operations, or visit the JSON routes from tools like Postman or curl.</p>
            </div>
        </body>
        </html>
        """
        return Response(html, mimetype='text/html')

    return jsonify({
        "message": "Inventory Management System API",
        "version": "1.0.0",
        "author": "Kosh",
        "endpoints": {
            "GET /inventory": "Fetch all inventory items",
            "GET /inventory/<id>": "Fetch single inventory item",
            "POST /inventory": "Add new inventory item",
            "PATCH /inventory/<id>": "Update inventory item",
            "DELETE /inventory/<id>": "Remove inventory item",
            "GET /api/search/barcode/<barcode>": "Search OpenFoodFacts by barcode",
            "GET /api/search/name/<name>": "Search OpenFoodFacts by product name",
            "POST /api/inventory/add-from-api": "Add item from OpenFoodFacts API"
        }
    })

# READ ALL - GET /inventory
@app.route('/inventory', methods=['GET'])
def get_all_inventory():
    """
    Fetch all inventory items
    Returns: List of all inventory items with 200 status
    """
    try:
        # Optional query parameters for filtering
        category = request.args.get('category')
        brand = request.args.get('brand')

        items = inventory_db

        # Apply filters if provided
        if category:
            items = [item for item in items if item.get('category', '').lower() == category.lower()]
        if brand:
            items = [item for item in items if item.get('brand', '').lower() == brand.lower()]

        return jsonify({
            "status": "success",
            "count": len(items),
            "data": items
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error fetching inventory: {str(e)}"
        }), 500

# READ ONE - GET /inventory/<id>
@app.route('/inventory/<item_id>', methods=['GET'])
def get_inventory_item(item_id):
    """
    Fetch a single inventory item by ID
    Returns: Single item with 200 status or 404 if not found
    """
    try:
        item = find_item_by_id(item_id)
        if item:
            return jsonify({
                "status": "success",
                "data": item
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"Item with ID '{item_id}' not found"
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error fetching item: {str(e)}"
        }), 500

# CREATE - POST /inventory
@app.route('/inventory', methods=['POST'])
def add_inventory_item():
    """
    Add a new inventory item
    Required fields: product_name, stock_level, price
    Optional: brand, category, description, barcode
    Returns: Created item with 201 status
    """
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided. Please provide item details in JSON format."
            }), 400

        # Validate required fields
        required_fields = ['product_name', 'stock_level', 'price']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Create new inventory item
        new_item = {
            "id": generate_id(),
            "product_name": data['product_name'],
            "brand": data.get('brand', 'Unknown'),
            "category": data.get('category', 'Uncategorized'),
            "description": data.get('description', ''),
            "stock_level": int(data['stock_level']),
            "price": float(data['price']),
            "barcode": data.get('barcode', ''),
            "ingredients": data.get('ingredients', ''),
            "nutriscore_grade": data.get('nutriscore_grade', 'N/A'),
            "image_url": data.get('image_url', ''),
            "quantity": data.get('quantity', 'N/A'),
            "source": data.get('source', 'Manual Entry'),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        inventory_db.append(new_item)

        return jsonify({
            "status": "success",
            "message": "Item added successfully",
            "data": new_item
        }), 201

    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error adding item: {str(e)}"
        }), 500

# UPDATE - PATCH /inventory/<id>
@app.route('/inventory/<item_id>', methods=['PATCH'])
def update_inventory_item(item_id):
    """
    Update an existing inventory item (partial update)
    Accepts any combination of fields to update
    Returns: Updated item with 200 status or 404 if not found
    """
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "status": "error",
                "message": "No update data provided"
            }), 400

        item_index = find_item_index(item_id)

        if item_index == -1:
            return jsonify({
                "status": "error",
                "message": f"Item with ID '{item_id}' not found"
            }), 404

        item = inventory_db[item_index]

        # Fields that can be updated
        updatable_fields = [
            'product_name', 'brand', 'category', 'description',
            'stock_level', 'price', 'barcode', 'ingredients',
            'nutriscore_grade', 'image_url', 'quantity'
        ]

        # Update only provided fields
        for field in updatable_fields:
            if field in data:
                if field in ['stock_level']:
                    item[field] = int(data[field])
                elif field in ['price']:
                    item[field] = float(data[field])
                else:
                    item[field] = data[field]

        item['updated_at'] = datetime.now().isoformat()

        return jsonify({
            "status": "success",
            "message": "Item updated successfully",
            "data": item
        }), 200

    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error updating item: {str(e)}"
        }), 500

# DELETE - DELETE /inventory/<id>
@app.route('/inventory/<item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    """
    Remove an inventory item by ID
    Returns: Success message with 200 status or 404 if not found
    """
    try:
        item_index = find_item_index(item_id)

        if item_index == -1:
            return jsonify({
                "status": "error",
                "message": f"Item with ID '{item_id}' not found"
            }), 404

        deleted_item = inventory_db.pop(item_index)

        return jsonify({
            "status": "success",
            "message": f"Item '{deleted_item['product_name']}' deleted successfully",
            "deleted_item": deleted_item
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error deleting item: {str(e)}"
        }), 500

# =============================================================================
# EXTERNAL API ROUTES - OpenFoodFacts Integration
# =============================================================================

@app.route('/api/search/barcode/<barcode>', methods=['GET'])
def search_by_barcode(barcode):
    """
    Search OpenFoodFacts API by barcode
    Returns: Product details if found
    """
    try:
        product = fetch_product_by_barcode(barcode)

        if product:
            return jsonify({
                "status": "success",
                "source": "OpenFoodFacts",
                "data": product
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"No product found for barcode: {barcode}"
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error searching by barcode: {str(e)}"
        }), 500

@app.route('/api/search/name/<product_name>', methods=['GET'])
def search_by_name(product_name):
    """
    Search OpenFoodFacts API by product name
    Returns: List of matching products
    """
    try:
        products = fetch_product_by_name(product_name)

        if products:
            return jsonify({
                "status": "success",
                "source": "OpenFoodFacts",
                "count": len(products),
                "data": products
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"No products found for name: {product_name}"
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error searching by name: {str(e)}"
        }), 500

@app.route('/api/inventory/add-from-api', methods=['POST'])
def add_item_from_api():
    """
    Add inventory item from OpenFoodFacts API data
    Requires: barcode and stock_level/price in request body
    Returns: Created item with 201 status
    """
    try:
        data = request.get_json(silent=True)

        if not data or 'barcode' not in data:
            return jsonify({
                "status": "error",
                "message": "Barcode is required in request body"
            }), 400

        barcode = data['barcode']

        # Fetch product from OpenFoodFacts
        product = fetch_product_by_barcode(barcode)

        if not product:
            return jsonify({
                "status": "error",
                "message": f"No product found for barcode: {barcode}"
            }), 404

        # Create inventory item with API data + user provided data
        new_item = {
            "id": generate_id(),
            "product_name": product['product_name'],
            "brand": product['brands'],
            "category": product.get('categories', 'Uncategorized').split(',')[0] if product.get('categories') else 'Uncategorized',
            "description": product['ingredients_text'],
            "stock_level": int(data.get('stock_level', 0)),
            "price": float(data.get('price', 0.0)),
            "barcode": barcode,
            "ingredients": product['ingredients_text'],
            "nutriscore_grade": product['nutriscore_grade'],
            "image_url": product['image_url'],
            "quantity": product['quantity'],
            "source": "OpenFoodFacts API",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        inventory_db.append(new_item)

        return jsonify({
            "status": "success",
            "message": "Item added from OpenFoodFacts API successfully",
            "data": new_item
        }), 201

    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error adding item from API: {str(e)}"
        }), 500

# =============================================================================
# HELPER ROUTES
# =============================================================================

@app.route('/inventory/stats', methods=['GET'])
def get_inventory_stats():
    """Get inventory statistics"""
    try:
        total_items = len(inventory_db)
        total_value = sum(item['price'] * item['stock_level'] for item in inventory_db)
        categories = list(set(item.get('category', 'Uncategorized') for item in inventory_db))

        return jsonify({
            "status": "success",
            "stats": {
                "total_items": total_items,
                "total_inventory_value": round(total_value, 2),
                "categories": categories,
                "low_stock_items": [item for item in inventory_db if item['stock_level'] < 10]
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error fetching stats: {str(e)}"
        }), 500

@app.route('/inventory/seed', methods=['POST'])
def seed_database():
    """Seed database with mock data resembling OpenFoodFacts format"""
    try:
        mock_data = [
            {
                "id": generate_id(),
                "product_name": "Organic Almond Milk",
                "brand": "Silk",
                "category": "Beverages",
                "description": "Filtered water, almonds, cane sugar, sea salt, locust bean gum, gellan gum, natural flavor, sunflower lecithin, vitamin D2, vitamin E",
                "stock_level": 45,
                "price": 3.99,
                "barcode": "025293600232",
                "ingredients": "Filtered water, almonds, cane sugar, sea salt, locust bean gum, gellan gum, natural flavor, sunflower lecithin, vitamin D2, vitamin E",
                "nutriscore_grade": "B",
                "image_url": "https://images.openfoodfacts.org/images/products/025/293/600/232/front_en.123.400.jpg",
                "quantity": "946 ml",
                "source": "OpenFoodFacts",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": generate_id(),
                "product_name": "Whole Wheat Bread",
                "brand": "Dave's Killer Bread",
                "category": "Bakery",
                "description": "Whole wheat flour, water, organic cane sugar, yeast, sea salt, organic wheat gluten, organic vinegar, organic oat fiber, organic molasses",
                "stock_level": 23,
                "price": 5.49,
                "barcode": "013764027382",
                "ingredients": "Whole wheat flour, water, organic cane sugar, yeast, sea salt, organic wheat gluten, organic vinegar, organic oat fiber, organic molasses",
                "nutriscore_grade": "A",
                "image_url": "https://images.openfoodfacts.org/images/products/013/764/027/382/front_en.456.400.jpg",
                "quantity": "680 g",
                "source": "OpenFoodFacts",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": generate_id(),
                "product_name": "Greek Yogurt Plain",
                "brand": "Fage",
                "category": "Dairy",
                "description": "Grade A pasteurized skimmed milk and cream, live active yogurt cultures",
                "stock_level": 67,
                "price": 6.29,
                "barcode": "006890763832",
                "ingredients": "Grade A pasteurized skimmed milk and cream, live active yogurt cultures",
                "nutriscore_grade": "A",
                "image_url": "https://images.openfoodfacts.org/images/products/006/890/763/832/front_en.789.400.jpg",
                "quantity": "1000 g",
                "source": "OpenFoodFacts",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": generate_id(),
                "product_name": "Organic Quinoa",
                "brand": "Ancient Harvest",
                "category": "Grains",
                "description": "Organic white quinoa",
                "stock_level": 34,
                "price": 7.99,
                "barcode": "007341620102",
                "ingredients": "Organic white quinoa",
                "nutriscore_grade": "A",
                "image_url": "https://images.openfoodfacts.org/images/products/007/341/620/102/front_en.012.400.jpg",
                "quantity": "368 g",
                "source": "OpenFoodFacts",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": generate_id(),
                "product_name": "Sparkling Water Lemon",
                "brand": "LaCroix",
                "category": "Beverages",
                "description": "Carbonated water, natural lemon flavor",
                "stock_level": 89,
                "price": 4.99,
                "barcode": "001299300120",
                "ingredients": "Carbonated water, natural lemon flavor",
                "nutriscore_grade": "A",
                "image_url": "https://images.openfoodfacts.org/images/products/001/299/300/120/front_en.345.400.jpg",
                "quantity": "355 ml x 8",
                "source": "OpenFoodFacts",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]

        inventory_db.extend(mock_data)

        return jsonify({
            "status": "success",
            "message": f"Database seeded with {len(mock_data)} items",
            "data": mock_data
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error seeding database: {str(e)}"
        }), 500

@app.route('/inventory/clear', methods=['DELETE'])
def clear_database():
    """Clear all inventory items (for testing purposes)"""
    try:
        count = len(inventory_db)
        inventory_db.clear()

        return jsonify({
            "status": "success",
            "message": f"Database cleared. {count} items removed."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing database: {str(e)}"
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found. Please check the API documentation."
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "status": "error",
        "message": "Method not allowed for this endpoint."
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error occurred."
    }), 500

if __name__ == '__main__':
    # Run with debug mode for development
    app.run(debug=True, host='0.0.0.0', port=5000)
