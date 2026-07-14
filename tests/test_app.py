"""
Inventory Management System - Test Suite
Author: Kosh
Repository: https://github.com/Ck-kosh/Python-REST-API-with-Flask--Inventory-summative-lab1.git

This module contains unit tests for:
- API endpoints (GET, POST, PATCH, DELETE)
- CLI commands
- External API interactions (OpenFoodFacts)
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app, inventory_db, fetch_product_by_barcode, fetch_product_by_name, generate_id

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_item():
    """Return a sample inventory item for testing"""
    return {
        "product_name": "Test Product",
        "brand": "Test Brand",
        "category": "Test Category",
        "description": "A test product description",
        "stock_level": 50,
        "price": 9.99,
        "barcode": "1234567890123"
    }


@pytest.fixture
def mock_openfoodfacts_response():
    """Return a mock OpenFoodFacts API response"""
    return {
        "status": 1,
        "product": {
            "product_name": "Mock Product",
            "brands": "Mock Brand",
            "ingredients_text": "Mock ingredients",
            "nutriscore_grade": "b",
            "categories": "Beverages, Drinks",
            "image_url": "https://example.com/image.jpg",
            "quantity": "500 ml"
        }
    }

class TestFlaskRouting:
    """Tests for Flask routing and basic endpoint availability"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == "Inventory Management System API"
        assert 'endpoints' in data

    def test_404_handler(self, client):
        """Test 404 error handler for non-existent routes"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_405_handler(self, client):
        """Test 405 error handler for invalid methods"""
        response = client.post('/inventory/123')
        assert response.status_code == 405
        data = json.loads(response.data)
        assert data['status'] == 'error'

class TestCRUDOperations:
    """Tests for Create, Read, Update, Delete operations"""

    def test_get_all_inventory_empty(self, client):
        """Test GET /inventory returns empty list when no items"""
        # Clear inventory
        inventory_db.clear()

        response = client.get('/inventory')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == 0
        assert data['data'] == []

    def test_create_item(self, client, sample_item):
        """Test POST /inventory creates a new item"""
        inventory_db.clear()

        response = client.post('/inventory',
                              data=json.dumps(sample_item),
                              content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Item added successfully'
        assert 'data' in data
        assert data['data']['product_name'] == sample_item['product_name']
        assert data['data']['stock_level'] == sample_item['stock_level']
        assert data['data']['price'] == sample_item['price']
        assert 'id' in data['data']
        assert 'created_at' in data['data']

    def test_create_item_missing_required_fields(self, client):
        """Test POST /inventory fails with missing required fields"""
        inventory_db.clear()

        incomplete_item = {"product_name": "Incomplete"}

        response = client.post('/inventory',
                              data=json.dumps(incomplete_item),
                              content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing required fields' in data['message']

    def test_create_item_invalid_json(self, client):
        """Test POST /inventory fails with invalid JSON"""
        response = client.post('/inventory',
                              data="not json",
                              content_type='application/json')

        assert response.status_code == 400

    def test_get_single_item(self, client, sample_item):
        """Test GET /inventory/<id> returns specific item"""
        inventory_db.clear()

        # Create item first
        post_response = client.post('/inventory',
                                   data=json.dumps(sample_item),
                                   content_type='application/json')
        created_item = json.loads(post_response.data)['data']
        item_id = created_item['id']

        # Get the item
        response = client.get(f'/inventory/{item_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['id'] == item_id

    def test_get_single_item_not_found(self, client):
        """Test GET /inventory/<id> returns 404 for non-existent item"""
        response = client.get('/inventory/nonexistent-id')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'not found' in data['message']

    def test_update_item(self, client, sample_item):
        """Test PATCH /inventory/<id> updates an item"""
        inventory_db.clear()

        # Create item first
        post_response = client.post('/inventory',
                                   data=json.dumps(sample_item),
                                   content_type='application/json')
        created_item = json.loads(post_response.data)['data']
        item_id = created_item['id']

        # Update the item
        updates = {
            "price": 14.99,
            "stock_level": 75
        }

        response = client.patch(f'/inventory/{item_id}',
                               data=json.dumps(updates),
                               content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['price'] == 14.99
        assert data['data']['stock_level'] == 75
        assert data['data']['product_name'] == sample_item['product_name']  # Unchanged

    def test_update_item_not_found(self, client):
        """Test PATCH /inventory/<id> returns 404 for non-existent item"""
        response = client.patch('/inventory/nonexistent-id',
                               data=json.dumps({"price": 10.00}),
                               content_type='application/json')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_update_item_no_data(self, client, sample_item):
        """Test PATCH /inventory/<id> fails with no update data"""
        inventory_db.clear()

        post_response = client.post('/inventory',
                                   data=json.dumps(sample_item),
                                   content_type='application/json')
        item_id = json.loads(post_response.data)['data']['id']

        response = client.patch(f'/inventory/{item_id}',
                               data=json.dumps({}),
                               content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_delete_item(self, client, sample_item):
        """Test DELETE /inventory/<id> removes an item"""
        inventory_db.clear()

        # Create item first
        post_response = client.post('/inventory',
                                   data=json.dumps(sample_item),
                                   content_type='application/json')
        created_item = json.loads(post_response.data)['data']
        item_id = created_item['id']

        # Delete the item
        response = client.delete(f'/inventory/{item_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'deleted' in data['message'].lower()

        # Verify item is gone
        get_response = client.get(f'/inventory/{item_id}')
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client):
        """Test DELETE /inventory/<id> returns 404 for non-existent item"""
        response = client.delete('/inventory/nonexistent-id')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'



class TestExternalAPI:
    """Tests for OpenFoodFacts API integration"""

    @patch('app.requests.get')
    def test_fetch_product_by_barcode_success(self, mock_get, mock_openfoodfacts_response):
        """Test successful barcode lookup"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openfoodfacts_response
        mock_get.return_value = mock_response

        result = fetch_product_by_barcode("123456789")

        assert result is not None
        assert result['product_name'] == 'Mock Product'
        assert result['brands'] == 'Mock Brand'
        assert result['source'] == 'OpenFoodFacts'

    @patch('app.requests.get')
    def test_fetch_product_by_barcode_not_found(self, mock_get):
        """Test barcode lookup when product not found"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 0, "status_verbose": "not found"}
        mock_get.return_value = mock_response

        result = fetch_product_by_barcode("000000000")

        assert result is None

    @patch('app.requests.get')
    def test_fetch_product_by_barcode_api_error(self, mock_get):
        """Test barcode lookup when API request fails"""
        mock_get.side_effect = Exception("Connection error")

        result = fetch_product_by_barcode("123456789")

        assert result is None

    @patch('app.requests.get')
    def test_fetch_product_by_name_success(self, mock_get, mock_openfoodfacts_response):
        """Test successful product name search"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [mock_openfoodfacts_response['product']]
        }
        mock_get.return_value = mock_response

        results = fetch_product_by_name("Mock Product")

        assert len(results) == 1
        assert results[0]['product_name'] == 'Mock Product'

    @patch('app.requests.get')
    def test_fetch_product_by_name_no_results(self, mock_get):
        """Test product name search with no results"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": []}
        mock_get.return_value = mock_response

        results = fetch_product_by_name("NonExistentProduct12345")

        assert results == []

    @patch('app.requests.get')
    def test_search_by_barcode_endpoint(self, mock_get, client, mock_openfoodfacts_response):
        """Test GET /api/search/barcode/<barcode> endpoint"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openfoodfacts_response
        mock_get.return_value = mock_response

        response = client.get('/api/search/barcode/123456789')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['source'] == 'OpenFoodFacts'
        assert data['data']['product_name'] == 'Mock Product'

    @patch('app.requests.get')
    def test_search_by_name_endpoint(self, mock_get, client, mock_openfoodfacts_response):
        """Test GET /api/search/name/<name> endpoint"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [mock_openfoodfacts_response['product']]
        }
        mock_get.return_value = mock_response

        response = client.get('/api/search/name/Mock%20Product')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == 1

    @patch('app.requests.get')
    def test_add_item_from_api_endpoint(self, mock_get, client, mock_openfoodfacts_response):
        """Test POST /api/inventory/add-from-api endpoint"""
        inventory_db.clear()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openfoodfacts_response
        mock_get.return_value = mock_response

        response = client.post('/api/inventory/add-from-api',
                              data=json.dumps({
                                  "barcode": "123456789",
                                  "stock_level": 25,
                                  "price": 5.99
                              }),
                              content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['product_name'] == 'Mock Product'
        assert data['data']['stock_level'] == 25
        assert data['data']['price'] == 5.99
        assert data['data']['source'] == 'OpenFoodFacts API'

    def test_add_item_from_api_missing_barcode(self, client):
        """Test POST /api/inventory/add-from-api fails without barcode"""
        response = client.post('/api/inventory/add-from-api',
                              data=json.dumps({"stock_level": 10}),
                              content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'



class TestHelperRoutes:
    """Tests for helper/utility routes"""

    def test_seed_database(self, client):
        """Test POST /inventory/seed adds mock data"""
        inventory_db.clear()

        response = client.post('/inventory/seed')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'seeded' in data['message'].lower()
        assert len(inventory_db) == 5

    def test_clear_database(self, client):
        """Test DELETE /inventory/clear removes all items"""
        inventory_db.clear()

        # Add a test item
        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "Test",
                       "stock_level": 10,
                       "price": 1.00
                   }),
                   content_type='application/json')

        assert len(inventory_db) == 1

        response = client.delete('/inventory/clear')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(inventory_db) == 0

    def test_inventory_stats(self, client):
        """Test GET /inventory/stats returns statistics"""
        inventory_db.clear()

        # Add test items
        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "Item1",
                       "stock_level": 10,
                       "price": 5.00
                   }),
                   content_type='application/json')

        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "Item2",
                       "stock_level": 5,
                       "price": 10.00
                   }),
                   content_type='application/json')

        response = client.get('/inventory/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['stats']['total_items'] == 2
        assert data['stats']['total_inventory_value'] == 100.00


class TestFiltering:
    """Tests for query parameter filtering"""

    def test_filter_by_category(self, client):
        """Test GET /inventory?category= filters by category"""
        inventory_db.clear()

        # Add items with different categories
        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "Beverage1",
                       "stock_level": 10,
                       "price": 2.00,
                       "category": "Beverages"
                   }),
                   content_type='application/json')

        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "Food1",
                       "stock_level": 5,
                       "price": 5.00,
                       "category": "Food"
                   }),
                   content_type='application/json')

        response = client.get('/inventory?category=Beverages')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['data'][0]['category'] == 'Beverages'

    def test_filter_by_brand(self, client):
        """Test GET /inventory?brand= filters by brand"""
        inventory_db.clear()

        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "BrandA Product",
                       "stock_level": 10,
                       "price": 2.00,
                       "brand": "BrandA"
                   }),
                   content_type='application/json')

        client.post('/inventory',
                   data=json.dumps({
                       "product_name": "BrandB Product",
                       "stock_level": 5,
                       "price": 5.00,
                       "brand": "BrandB"
                   }),
                   content_type='application/json')

        response = client.get('/inventory?brand=BrandA')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['data'][0]['brand'] == 'BrandA'



class TestIDGeneration:
    """Tests for ID generation utility"""

    def test_generate_id_unique(self):
        """Test that generated IDs are unique"""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2

    def test_generate_id_format(self):
        """Test that generated IDs are valid UUIDs"""
        id_val = generate_id()
        assert len(id_val) == 36  # UUID length with hyphens
        assert '-' in id_val



class TestDataValidation:
    """Tests for input data validation"""

    def test_create_item_invalid_stock_level(self, client):
        """Test POST /inventory fails with non-integer stock_level"""
        response = client.post('/inventory',
                              data=json.dumps({
                                  "product_name": "Test",
                                  "stock_level": "not_a_number",
                                  "price": 5.00
                              }),
                              content_type='application/json')

        assert response.status_code == 400

    def test_create_item_invalid_price(self, client):
        """Test POST /inventory fails with non-float price"""
        response = client.post('/inventory',
                              data=json.dumps({
                                  "product_name": "Test",
                                  "stock_level": 10,
                                  "price": "not_a_number"
                              }),
                              content_type='application/json')

        assert response.status_code == 400

    def test_update_item_invalid_data_types(self, client, sample_item):
        """Test PATCH /inventory/<id> fails with invalid data types"""
        inventory_db.clear()

        post_response = client.post('/inventory',
                                   data=json.dumps(sample_item),
                                   content_type='application/json')
        item_id = json.loads(post_response.data)['data']['id']

        response = client.patch(f'/inventory/{item_id}',
                               data=json.dumps({"price": "invalid"}),
                               content_type='application/json')

        assert response.status_code == 400


# TEST: CLI COMMANDS (Integration Tests)

class TestCLIIntegration:
    """Integration tests simulating CLI interactions"""

    def test_full_crud_workflow(self, client):
        """Test complete CRUD workflow through API"""
        inventory_db.clear()

        # CREATE
        create_response = client.post('/inventory',
                                     data=json.dumps({
                                         "product_name": "Workflow Test",
                                         "stock_level": 100,
                                         "price": 15.99
                                     }),
                                     content_type='application/json')
        assert create_response.status_code == 201
        item_id = json.loads(create_response.data)['data']['id']

        # READ
        read_response = client.get(f'/inventory/{item_id}')
        assert read_response.status_code == 200
        assert json.loads(read_response.data)['data']['product_name'] == 'Workflow Test'

        # UPDATE
        update_response = client.patch(f'/inventory/{item_id}',
                                      data=json.dumps({"price": 19.99}),
                                      content_type='application/json')
        assert update_response.status_code == 200
        assert json.loads(update_response.data)['data']['price'] == 19.99

        # DELETE
        delete_response = client.delete(f'/inventory/{item_id}')
        assert delete_response.status_code == 200

        # VERIFY DELETION
        verify_response = client.get(f'/inventory/{item_id}')
        assert verify_response.status_code == 404

    def test_api_search_and_add_workflow(self, client):
        """Test searching API and adding to inventory workflow"""
        inventory_db.clear()

        with patch('app.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": 1,
                "product": {
                    "product_name": "API Product",
                    "brands": "API Brand",
                    "ingredients_text": "Test ingredients",
                    "nutriscore_grade": "a",
                    "categories": "Test Category",
                    "image_url": "",
                    "quantity": "100g"
                }
            }
            mock_get.return_value = mock_response

            # Search by barcode
            search_response = client.get('/api/search/barcode/12345')
            assert search_response.status_code == 200

            # Add from API
            add_response = client.post('/api/inventory/add-from-api',
                                      data=json.dumps({
                                          "barcode": "12345",
                                          "stock_level": 50,
                                          "price": 8.99
                                      }),
                                      content_type='application/json')
            assert add_response.status_code == 201

            # Verify in inventory
            inventory_response = client.get('/inventory')
            assert json.loads(inventory_response.data)['count'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
