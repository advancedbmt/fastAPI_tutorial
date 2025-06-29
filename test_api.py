#=======================================================================
# FastAPI API Testing Suite
#=======================================================================

# Multiple approaches: pytest with TestClient, requests, and async tests

# Install dependencies
# pip install pytest httpx requests

# Run pytest tests (no server needed)
# pytest test_api.py -v

# Run live API tests (server must be running)
# python test_api.py

# Run specific test class
# pytest test_api.py::TestFastAPIEndpoints -v
        
# =============================================================
# Method 1: Using pytest with FastAPI TestClient (Recommended)
# =============================================================

# test_api.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json

# Import your FastAPI app
from app.main import app

client = TestClient(app)

class TestFastAPIEndpoints:
    """Test suite for FastAPI User Management API using TestClient"""

    def setup_method(self):
        """Setup method run before each test"""
        # Clear any existing users
        response = client.get("/users/")
        users = response.json()
        for user in users:
            client.delete(f"/users/{user['id']}")

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome to the User Management API" in response.json()["message"]

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert data["age"] == user_data["age"]
        assert data["id"] is not None
        assert data["is_active"] is True
        assert "created_at" in data

    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email"""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        # Create first user
        response1 = client.post("/users/", json=user_data)
        assert response1.status_code == 201

        # Try to create duplicate
        user_data["name"] = "Jane Doe"
        response2 = client.post("/users/", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    def test_create_user_validation_errors(self):
        """Test user creation with validation errors"""
        # Missing required fields
        response = client.post("/users/", json={})
        assert response.status_code == 422

        # Invalid age
        invalid_user = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": -5
        }
        response = client.post("/users/", json=invalid_user)
        assert response.status_code == 422

        # Invalid email format
        invalid_user = {
            "name": "John Doe",
            "email": "invalid-email",
            "age": 30
        }
        response = client.post("/users/", json=invalid_user)
        assert response.status_code == 422

    def test_get_users_empty(self):
        """Test getting users when none exist"""
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_users_with_data(self):
        """Test getting users with existing data"""
        # Create test users
        users_data = [
            {"name": "John Doe", "email": "john@example.com", "age": 30},
            {"name": "Jane Smith", "email": "jane@example.com", "age": 25}
        ]

        created_users = []
        for user_data in users_data:
            response = client.post("/users/", json=user_data)
            created_users.append(response.json())

        # Get all users
        response = client.get("/users/")
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 2

        # Verify user data
        for created_user in created_users:
            assert any(u["id"] == created_user["id"] for u in users)

    def test_get_users_pagination(self):
        """Test user pagination"""
        # Create multiple users
        for i in range(5):
            user_data = {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + i
            }
            client.post("/users/", json=user_data)

        # Test pagination
        response = client.get("/users/?skip=2&limit=2")
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 2

    def test_get_user_by_id_success(self):
        """Test getting user by ID successfully"""
        # Create user
        user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}
        create_response = client.post("/users/", json=user_data)
        created_user = create_response.json()

        # Get user by ID
        response = client.get(f"/users/{created_user['id']}")
        assert response.status_code == 200
        user = response.json()
        assert user["id"] == created_user["id"]
        assert user["name"] == user_data["name"]

    def test_get_user_by_id_not_found(self):
        """Test getting non-existent user"""
        response = client.get("/users/999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_update_user_success(self):
        """Test successful user update"""
        # Create user
        user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}
        create_response = client.post("/users/", json=user_data)
        created_user = create_response.json()

        # Update user
        update_data = {"name": "John Smith", "age": 31}
        response = client.put(f"/users/{created_user['id']}", json=update_data)
        assert response.status_code == 200

        updated_user = response.json()
        assert updated_user["name"] == "John Smith"
        assert updated_user["age"] == 31
        assert updated_user["email"] == user_data["email"]  # Unchanged

    def test_update_user_not_found(self):
        """Test updating non-existent user"""
        update_data = {"name": "John Smith"}
        response = client.put("/users/999", json=update_data)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_update_user_duplicate_email(self):
        """Test updating user with duplicate email"""
        # Create two users
        user1_data = {"name": "John Doe", "email": "john@example.com", "age": 30}
        user2_data = {"name": "Jane Smith", "email": "jane@example.com", "age": 25}

        user1_response = client.post("/users/", json=user1_data)
        user2_response = client.post("/users/", json=user2_data)

        user1 = user1_response.json()
        user2 = user2_response.json()

        # Try to update user2 with user1's email
        update_data = {"email": "john@example.com"}
        response = client.put(f"/users/{user2['id']}", json=update_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_delete_user_success(self):
        """Test successful user deletion"""
        # Create user
        user_data = {"name": "John Doe", "email": "john@example.com", "age": 30}
        create_response = client.post("/users/", json=user_data)
        created_user = create_response.json()

        # Delete user
        response = client.delete(f"/users/{created_user['id']}")
        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/users/{created_user['id']}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self):
        """Test deleting non-existent user"""
        response = client.delete("/users/999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


# ======================================================
# Method 2: Using requests library for live API testing
# ======================================================

import requests
import time

class LiveAPITester:
    """Test suite for live FastAPI server using requests"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.created_user_ids = []

    def cleanup(self):
        """Clean up created users"""
        for user_id in self.created_user_ids:
            try:
                self.session.delete(f"{self.base_url}/users/{user_id}")
            except:
                pass
        self.created_user_ids.clear()

    def test_api_availability(self):
        """Test if API is available"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            print(f"✅ API Health Check: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"❌ API not available: {e}")
            return False

    def test_create_user(self):
        """Test creating a user via live API"""
        user_data = {
            "name": "Test User",
            "email": f"test{int(time.time())}@example.com",
            "age": 25
        }

        try:
            response = self.session.post(
                f"{self.base_url}/users/", 
                json=user_data,
                timeout=5
            )
            print(f"✅ Create User: {response.status_code}")

            if response.status_code == 201:
                user = response.json()
                self.created_user_ids.append(user["id"])
                print(f"   Created user ID: {user['id']}")
                return user
            else:
                print(f"   Error: {response.json()}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Create User failed: {e}")
            return None

    def test_get_users(self):
        """Test getting all users"""
        try:
            response = self.session.get(f"{self.base_url}/users/", timeout=5)
            print(f"✅ Get Users: {response.status_code}")

            if response.status_code == 200:
                users = response.json()
                print(f"   Found {len(users)} users")
                return users
            else:
                print(f"   Error: {response.json()}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Get Users failed: {e}")
            return None

    def test_get_user_by_id(self, user_id):
        """Test getting user by ID"""
        try:
            response = self.session.get(f"{self.base_url}/users/{user_id}", timeout=5)
            print(f"✅ Get User by ID: {response.status_code}")

            if response.status_code == 200:
                user = response.json()
                print(f"   User: {user['name']} ({user['email']})")
                return user
            else:
                print(f"   Error: {response.json()}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Get User by ID failed: {e}")
            return None

    def test_update_user(self, user_id):
        """Test updating a user"""
        update_data = {
            "name": "Updated Test User",
            "age": 30
        }

        try:
            response = self.session.put(
                f"{self.base_url}/users/{user_id}",
                json=update_data,
                timeout=5
            )
            print(f"✅ Update User: {response.status_code}")

            if response.status_code == 200:
                user = response.json()
                print(f"   Updated user: {user['name']}, age: {user['age']}")
                return user
            else:
                print(f"   Error: {response.json()}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Update User failed: {e}")
            return None

    def test_delete_user(self, user_id):
        """Test deleting a user"""
        try:
            response = self.session.delete(f"{self.base_url}/users/{user_id}", timeout=5)
            print(f"✅ Delete User: {response.status_code}")

            if response.status_code == 204:
                print(f"   User {user_id} deleted successfully")
                return True
            else:
                print(f"   Error: {response.json()}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Delete User failed: {e}")
            return False

    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Starting Live API Test Suite")
        print("=" * 50)

        # Test API availability
        if not self.test_api_availability():
            print("❌ API not available. Make sure the FastAPI server is running.")
            return

        # Test create user
        user = self.test_create_user()
        if not user:
            print("❌ Cannot continue without creating a user")
            return

        user_id = user["id"]

        # Test get all users
        self.test_get_users()

        # Test get user by ID
        self.test_get_user_by_id(user_id)

        # Test update user
        self.test_update_user(user_id)

        # Test delete user
        self.test_delete_user(user_id)

        # Clean up
        self.cleanup()

        print("=" * 50)
        print("✅ Live API Test Suite Completed")


# ==========================================
# Method 3: Performance testing
# ==========================================

import concurrent.futures
import time
from typing import List

class PerformanceTester:
    """Simple performance testing for API endpoints"""

    def __init__(self, base_url="http://localhost:8000", index_start=0):
        self.base_url = base_url
        self.index_start = index_start

    def create_user_load_test(self, num_requests=10, num_threads=3):
        """Load test user creation endpoint"""
        print(f"🔥 Load Testing: Creating {num_requests} users with {num_threads} threads")

        def create_single_user(index):
            """Create a single user"""
            user_data = {
                "name": f"Load Test User {index}",
                "email": f"loadtest{index}@example.com",
                "age": 20 + (index % 30)
            }

            start_time = time.time()
            try:
                response = requests.post(f"{self.base_url}/users/", json=user_data, timeout=10)
                end_time = time.time()

                return {
                    "success": response.status_code == 201,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "user_id": response.json().get("id") if response.status_code == 201 else None
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }

        # Execute load test
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_single_user, self.index_start + i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        response_times = [r["response_time"] for r in successful]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        print(f"📊 Load Test Results:")
        print(f"   Total requests: {num_requests}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Success rate: {len(successful)/num_requests*100:.1f}%")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Requests/second: {num_requests/total_time:.2f}")
        print(f"   Average response time: {avg_response_time:.3f}s")

        return results


# ==========================================
# Main execution and usage examples
# ==========================================

def main():
    """Main function demonstrating different testing approaches"""
    print("FastAPI Testing Suite")
    print("=" * 50)

    # Method 1: Run pytest tests (uncomment to run)
    # pytest.main(["-v", "test_api.py"])

    # Method 2: Live API testing
    print("\n🌐 Testing Live API...")
    live_tester = LiveAPITester()
    live_tester.run_full_test_suite()

    # Method 4: Performance testing (uncomment to run)
    print("\n⚡ Performance Testing...")
    perf_tester = PerformanceTester(index_start=100)
    perf_tester.create_user_load_test(num_requests=20, num_threads=5)

if __name__ == "__main__":
    main()


# ==========================================
# Requirements for running these tests
# ==========================================

"""
To run these tests, install the following packages:

pip install pytest httpx requests

Then run:

1. For pytest with TestClient (doesn't require running server):
   pytest test_api.py -v

2. For live API testing (requires running FastAPI server):
   python test_api.py

3. For async tests:
   pytest test_api.py::TestAsyncAPI -v

4. For specific test:
   pytest test_api.py::TestFastAPIEndpoints::test_create_user_success -v
"""
