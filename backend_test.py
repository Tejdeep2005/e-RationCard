import requests
import sys
import json
import base64
from datetime import datetime

class ERationAPITester:
    def __init__(self, base_url="https://rationportal-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.user_token = None
        self.admin_token = None
        self.test_user_id = None
        self.test_admin_id = None
        self.test_card_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, description=""):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        if description:
            print(f"   Description: {description}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                try:
                    return False, response.json()
                except:
                    return False, response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Test User {timestamp}",
            "email": f"testuser{timestamp}@example.com",
            "password": "TestPass123!",
            "phone": f"+1234567{timestamp}",
            "role": "user"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data,
            description="Register a new user account"
        )
        
        if success and 'token' in response:
            self.user_token = response['token']
            self.test_user_id = response['user']['id']
            return True
        return False

    def test_admin_registration(self):
        """Test admin registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        admin_data = {
            "name": f"Test Admin {timestamp}",
            "email": f"testadmin{timestamp}@example.com",
            "password": "AdminPass123!",
            "phone": f"+1234568{timestamp}",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Admin Registration",
            "POST",
            "auth/register",
            200,
            data=admin_data,
            description="Register a new admin account"
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.test_admin_id = response['user']['id']
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        # First register a user for login test
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Login Test User {timestamp}",
            "email": f"logintest{timestamp}@example.com",
            "password": "LoginTest123!",
            "phone": f"+1234569{timestamp}",
            "role": "user"
        }
        
        # Register first
        requests.post(f"{self.base_url}/auth/register", json=user_data)
        
        # Now test login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data,
            description="Login with valid credentials"
        )
        
        return success and 'token' in response

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200,
            token=self.user_token,
            description="Get authenticated user information"
        )
        
        return success and 'id' in response

    def test_apply_ration_card(self):
        """Test ration card application"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        # Create sample base64 data for files
        sample_image = base64.b64encode(b"fake_image_data").decode()
        sample_pdf = base64.b64encode(b"fake_pdf_data").decode()
        
        card_data = {
            "name": "Test Applicant",
            "address": "123 Test Street, Test City, Test State 12345",
            "family_members": 4,
            "aadhaar": "123456789012",
            "income_proof": f"data:application/pdf;base64,{sample_pdf}",
            "photo": f"data:image/jpeg;base64,{sample_image}"
        }
        
        success, response = self.run_test(
            "Apply Ration Card",
            "POST",
            "ration-cards/apply",
            200,
            data=card_data,
            token=self.user_token,
            description="Submit ration card application with AI verification"
        )
        
        if success and 'card' in response:
            self.test_card_id = response['card']['id']
            return True
        return False

    def test_get_my_card(self):
        """Test getting user's ration card"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        success, response = self.run_test(
            "Get My Ration Card",
            "GET",
            "ration-cards/my-card",
            200,
            token=self.user_token,
            description="Retrieve user's ration card details"
        )
        
        return success and 'id' in response

    def test_update_ration_card(self):
        """Test updating ration card"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        update_data = {
            "name": "Updated Test Applicant",
            "family_members": 5
        }
        
        success, response = self.run_test(
            "Update Ration Card",
            "PUT",
            "ration-cards/update",
            200,
            data=update_data,
            token=self.user_token,
            description="Update ration card details"
        )
        
        return success

    def test_admin_get_all_cards(self):
        """Test admin getting all cards"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Get All Cards",
            "GET",
            "admin/cards",
            200,
            token=self.admin_token,
            description="Admin retrieve all ration cards"
        )
        
        return success and isinstance(response, list)

    def test_admin_get_all_users(self):
        """Test admin getting all users"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Get All Users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token,
            description="Admin retrieve all users"
        )
        
        return success and isinstance(response, list)

    def test_admin_approve_card(self):
        """Test admin approving a card"""
        if not self.admin_token or not self.test_card_id:
            print("❌ Skipping - No admin token or card ID available")
            return False
            
        success, response = self.run_test(
            "Admin Approve Card",
            "PUT",
            f"admin/cards/{self.test_card_id}/approve",
            200,
            token=self.admin_token,
            description="Admin approve ration card application"
        )
        
        return success and 'card_number' in response

    def test_admin_reject_card(self):
        """Test admin rejecting a card"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        # Create another card to reject
        if self.user_token:
            sample_image = base64.b64encode(b"fake_image_data").decode()
            sample_pdf = base64.b64encode(b"fake_pdf_data").decode()
            
            card_data = {
                "name": "Test Reject Applicant",
                "address": "456 Reject Street, Test City",
                "family_members": 2,
                "aadhaar": "987654321098",
                "income_proof": f"data:application/pdf;base64,{sample_pdf}",
                "photo": f"data:image/jpeg;base64,{sample_image}"
            }
            
            # Apply for card first
            response = requests.post(
                f"{self.base_url}/ration-cards/apply",
                json=card_data,
                headers={'Authorization': f'Bearer {self.user_token}', 'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                reject_card_id = response.json()['card']['id']
                
                success, response = self.run_test(
                    "Admin Reject Card",
                    "PUT",
                    f"admin/cards/{reject_card_id}/reject",
                    200,
                    token=self.admin_token,
                    description="Admin reject ration card application"
                )
                
                return success
        
        return False

    def test_admin_distribute_tokens(self):
        """Test admin distributing SMS tokens"""
        if not self.admin_token or not self.test_user_id:
            print("❌ Skipping - No admin token or user ID available")
            return False
            
        token_data = {
            "user_ids": [self.test_user_id],
            "message": "Your ration collection token",
            "time_slot": "10:00 AM - 12:00 PM"
        }
        
        success, response = self.run_test(
            "Admin Distribute Tokens",
            "POST",
            "admin/distribute-tokens",
            200,
            data=token_data,
            token=self.admin_token,
            description="Admin send SMS tokens to users"
        )
        
        return success and 'sent_count' in response

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        success, response = self.run_test(
            "Unauthorized Access Test",
            "GET",
            "auth/me",
            401,
            description="Access protected endpoint without token"
        )
        
        return success

    def test_admin_only_access(self):
        """Test user trying to access admin endpoints"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        success, response = self.run_test(
            "Admin Only Access Test",
            "GET",
            "admin/cards",
            403,
            token=self.user_token,
            description="User trying to access admin endpoint"
        )
        
        return success

def main():
    print("🚀 Starting E-Ration Portal API Tests")
    print("=" * 50)
    
    tester = ERationAPITester()
    
    # Test sequence
    test_sequence = [
        ("User Registration", tester.test_user_registration),
        ("Admin Registration", tester.test_admin_registration),
        ("User Login", tester.test_user_login),
        ("Get Current User", tester.test_get_current_user),
        ("Apply Ration Card", tester.test_apply_ration_card),
        ("Get My Card", tester.test_get_my_card),
        ("Update Ration Card", tester.test_update_ration_card),
        ("Admin Get All Cards", tester.test_admin_get_all_cards),
        ("Admin Get All Users", tester.test_admin_get_all_users),
        ("Admin Approve Card", tester.test_admin_approve_card),
        ("Admin Reject Card", tester.test_admin_reject_card),
        ("Admin Distribute Tokens", tester.test_admin_distribute_tokens),
        ("Unauthorized Access", tester.test_unauthorized_access),
        ("Admin Only Access", tester.test_admin_only_access),
    ]
    
    # Run all tests
    for test_name, test_func in test_sequence:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            tester.failed_tests.append({
                "test": test_name,
                "error": str(e)
            })
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(tester.failed_tests)}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"{i}. {failure['test']}")
            if 'expected' in failure:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
                print(f"   Response: {failure['response']}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
    
    return 0 if len(tester.failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())