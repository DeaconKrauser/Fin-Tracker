#!/usr/bin/env python3
"""
Backend API Testing for Financial System
Tests authentication, transactions, categories, and dashboard APIs
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Backend URL from frontend .env
BASE_URL = "https://financas-tracker-3.preview.emergentagent.com/api"

class FinancialSystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        self.user_data = None
        self.test_results = {
            "authentication": {"passed": 0, "failed": 0, "details": []},
            "user_management": {"passed": 0, "failed": 0, "details": []},
            "transactions": {"passed": 0, "failed": 0, "details": []},
            "categories": {"passed": 0, "failed": 0, "details": []},
            "dashboard": {"passed": 0, "failed": 0, "details": []}
        }
        
    def log_result(self, category, test_name, passed, details=""):
        """Log test result"""
        if passed:
            self.test_results[category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.test_results[category]["failed"] += 1
            status = "❌ FAIL"
            
        self.test_results[category]["details"].append(f"{status}: {test_name} - {details}")
        print(f"{status}: {test_name} - {details}")
        
    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                print("✅ API Health Check: Backend is accessible")
                return True
            else:
                print(f"❌ API Health Check: Backend returned {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health Check: Cannot connect to backend - {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        test_user = {
            "email": "maria.silva@email.com",
            "name": "Maria Silva",
            "password": "senha123456"
        }
        
        try:
            response = requests.post(f"{self.base_url}/register", json=test_user, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.auth_token = data["access_token"]
                    self.user_data = data["user"]
                    self.log_result("authentication", "User Registration", True, 
                                  f"User {data['user']['name']} registered successfully")
                    return True
                else:
                    self.log_result("authentication", "User Registration", False, 
                                  "Missing token or user data in response")
                    return False
            else:
                error_msg = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_result("authentication", "User Registration", False, error_msg)
                return False
                
        except Exception as e:
            self.log_result("authentication", "User Registration", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        login_data = {
            "email": "maria.silva@email.com",
            "password": "senha123456"
        }
        
        try:
            response = requests.post(f"{self.base_url}/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    # Update token for subsequent tests
                    self.auth_token = data["access_token"]
                    self.user_data = data["user"]
                    self.log_result("authentication", "User Login", True, 
                                  f"Login successful for {data['user']['email']}")
                    return True
                else:
                    self.log_result("authentication", "User Login", False, 
                                  "Missing token or user data in response")
                    return False
            else:
                error_msg = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_result("authentication", "User Login", False, error_msg)
                return False
                
        except Exception as e:
            self.log_result("authentication", "User Login", False, f"Request failed: {str(e)}")
            return False
    
    def test_jwt_authentication(self):
        """Test JWT token validation"""
        if not self.auth_token:
            self.log_result("authentication", "JWT Token Validation", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/categories", headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.log_result("authentication", "JWT Token Validation", True, 
                              "Token successfully validated")
                return True
            elif response.status_code == 401:
                self.log_result("authentication", "JWT Token Validation", False, 
                              "Token validation failed - Unauthorized")
                return False
            else:
                self.log_result("authentication", "JWT Token Validation", False, 
                              f"Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("authentication", "JWT Token Validation", False, f"Request failed: {str(e)}")
            return False
    
    def test_default_categories_creation(self):
        """Test that default categories are created during registration"""
        if not self.auth_token:
            self.log_result("user_management", "Default Categories Creation", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/categories", headers=headers, timeout=10)
            
            if response.status_code == 200:
                categories = response.json()
                expected_categories = ["Salário", "Freelance", "Alimentação", "Transporte", "Lazer", "Contas"]
                found_categories = [cat["name"] for cat in categories]
                
                missing_categories = [cat for cat in expected_categories if cat not in found_categories]
                
                if not missing_categories:
                    self.log_result("user_management", "Default Categories Creation", True, 
                                  f"All {len(categories)} default categories created")
                    return True
                else:
                    self.log_result("user_management", "Default Categories Creation", False, 
                                  f"Missing categories: {missing_categories}")
                    return False
            else:
                self.log_result("user_management", "Default Categories Creation", False, 
                              f"Failed to fetch categories: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("user_management", "Default Categories Creation", False, f"Request failed: {str(e)}")
            return False
    
    def test_category_management(self):
        """Test category CRUD operations"""
        if not self.auth_token:
            self.log_result("categories", "Category Management", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test creating a new category
        new_category = {
            "name": "Investimentos",
            "type": "income"
        }
        
        try:
            # Create category
            response = requests.post(f"{self.base_url}/categories", json=new_category, headers=headers, timeout=10)
            
            if response.status_code == 200:
                created_category = response.json()
                self.log_result("categories", "Create Category", True, 
                              f"Category '{created_category['name']}' created successfully")
                
                # Test fetching categories
                response = requests.get(f"{self.base_url}/categories", headers=headers, timeout=10)
                if response.status_code == 200:
                    categories = response.json()
                    category_names = [cat["name"] for cat in categories]
                    if "Investimentos" in category_names:
                        self.log_result("categories", "Fetch Categories", True, 
                                      f"Found {len(categories)} categories including new one")
                        return True
                    else:
                        self.log_result("categories", "Fetch Categories", False, 
                                      "New category not found in list")
                        return False
                else:
                    self.log_result("categories", "Fetch Categories", False, 
                                  f"Failed to fetch categories: {response.status_code}")
                    return False
            else:
                error_msg = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_result("categories", "Create Category", False, error_msg)
                return False
                
        except Exception as e:
            self.log_result("categories", "Category Management", False, f"Request failed: {str(e)}")
            return False
    
    def test_transaction_operations(self):
        """Test transaction CRUD operations"""
        if not self.auth_token:
            self.log_result("transactions", "Transaction Operations", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # First get categories to use valid category_id
        try:
            response = requests.get(f"{self.base_url}/categories", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_result("transactions", "Transaction Operations", False, "Cannot fetch categories")
                return False
                
            categories = response.json()
            if not categories:
                self.log_result("transactions", "Transaction Operations", False, "No categories available")
                return False
                
            # Use first category for testing
            test_category_id = categories[0]["id"]
            
            # Test creating a transaction
            new_transaction = {
                "description": "Salário Janeiro",
                "amount": 5000.0,
                "type": "income",
                "category_id": test_category_id,
                "date": "2024-01-15"
            }
            
            response = requests.post(f"{self.base_url}/transactions", json=new_transaction, headers=headers, timeout=10)
            
            if response.status_code == 200:
                created_transaction = response.json()
                transaction_id = created_transaction["id"]
                self.log_result("transactions", "Create Transaction", True, 
                              f"Transaction '{created_transaction['description']}' created")
                
                # Test fetching transactions
                response = requests.get(f"{self.base_url}/transactions", headers=headers, timeout=10)
                if response.status_code == 200:
                    transactions = response.json()
                    transaction_descriptions = [t["description"] for t in transactions]
                    if "Salário Janeiro" in transaction_descriptions:
                        self.log_result("transactions", "Fetch Transactions", True, 
                                      f"Found {len(transactions)} transactions")
                        
                        # Test deleting transaction
                        response = requests.delete(f"{self.base_url}/transactions/{transaction_id}", headers=headers, timeout=10)
                        if response.status_code == 200:
                            self.log_result("transactions", "Delete Transaction", True, 
                                          "Transaction deleted successfully")
                            return True
                        else:
                            self.log_result("transactions", "Delete Transaction", False, 
                                          f"Delete failed: {response.status_code}")
                            return False
                    else:
                        self.log_result("transactions", "Fetch Transactions", False, 
                                      "Created transaction not found in list")
                        return False
                else:
                    self.log_result("transactions", "Fetch Transactions", False, 
                                  f"Failed to fetch transactions: {response.status_code}")
                    return False
            else:
                error_msg = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_result("transactions", "Create Transaction", False, error_msg)
                return False
                
        except Exception as e:
            self.log_result("transactions", "Transaction Operations", False, f"Request failed: {str(e)}")
            return False
    
    def test_dashboard_apis(self):
        """Test dashboard summary APIs"""
        if not self.auth_token:
            self.log_result("dashboard", "Dashboard APIs", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Test dashboard summary
            response = requests.get(f"{self.base_url}/dashboard/summary", headers=headers, timeout=10)
            
            if response.status_code == 200:
                summary = response.json()
                required_fields = ["total_income", "total_expense", "balance", "transactions_count"]
                
                if all(field in summary for field in required_fields):
                    self.log_result("dashboard", "Dashboard Summary", True, 
                                  f"Summary: Income={summary['total_income']}, Expense={summary['total_expense']}, Balance={summary['balance']}")
                else:
                    missing_fields = [field for field in required_fields if field not in summary]
                    self.log_result("dashboard", "Dashboard Summary", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_result("dashboard", "Dashboard Summary", False, 
                              f"Failed to fetch summary: {response.status_code}")
                return False
            
            # Test categories summary
            response = requests.get(f"{self.base_url}/dashboard/categories", headers=headers, timeout=10)
            
            if response.status_code == 200:
                categories_summary = response.json()
                self.log_result("dashboard", "Categories Summary", True, 
                              f"Found {len(categories_summary)} category summaries")
            else:
                self.log_result("dashboard", "Categories Summary", False, 
                              f"Failed to fetch categories summary: {response.status_code}")
                return False
            
            # Test monthly summary
            response = requests.get(f"{self.base_url}/dashboard/monthly", headers=headers, timeout=10)
            
            if response.status_code == 200:
                monthly_summary = response.json()
                self.log_result("dashboard", "Monthly Summary", True, 
                              f"Found {len(monthly_summary)} monthly summaries")
                return True
            else:
                self.log_result("dashboard", "Monthly Summary", False, 
                              f"Failed to fetch monthly summary: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("dashboard", "Dashboard APIs", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_isolation(self):
        """Test that users can only access their own data"""
        # This would require creating a second user and testing cross-access
        # For now, we'll just verify that authenticated requests work
        if not self.auth_token:
            self.log_result("authentication", "User Isolation", False, "No auth token")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Test that we can access our own data
            response = requests.get(f"{self.base_url}/transactions", headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.log_result("authentication", "User Data Access", True, 
                              "User can access their own data")
                return True
            else:
                self.log_result("authentication", "User Data Access", False, 
                              f"Cannot access own data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("authentication", "User Isolation", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Financial System Backend Tests")
        print(f"Testing backend at: {self.base_url}")
        print("=" * 60)
        
        # Test API health first
        if not self.test_api_health():
            print("❌ Backend is not accessible. Stopping tests.")
            return False
        
        print("\n📋 Testing Authentication System...")
        self.test_user_registration()
        self.test_user_login()
        self.test_jwt_authentication()
        self.test_user_isolation()
        
        print("\n👤 Testing User Management...")
        self.test_default_categories_creation()
        
        print("\n📁 Testing Category Management...")
        self.test_category_management()
        
        print("\n💰 Testing Transaction Operations...")
        self.test_transaction_operations()
        
        print("\n📊 Testing Dashboard APIs...")
        self.test_dashboard_apis()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 TEST SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            status = "✅" if failed == 0 else "❌"
            print(f"{status} {category.upper()}: {passed} passed, {failed} failed")
            
            if failed > 0:
                print("   Failed tests:")
                for detail in results["details"]:
                    if "❌ FAIL" in detail:
                        print(f"   - {detail}")
        
        print(f"\n🎯 OVERALL: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {total_failed} tests failed")
            return False

if __name__ == "__main__":
    tester = FinancialSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)