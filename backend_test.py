#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class VideoHostingAPITester:
    def __init__(self, base_url="https://streamnest-19.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if files:
                # Remove Content-Type for file uploads
                headers.pop('Content-Type', None)
                
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            must_change = response.get('must_change_password', False)
            print(f"   Token received, must_change_password: {must_change}")
            return True, must_change
        return False, False

    def test_change_password(self, current_password="admin123", new_password="NewSecurePass123!"):
        """Test password change"""
        success, response = self.run_test(
            "Change Password",
            "POST",
            "auth/change-password",
            200,
            data={"current_password": current_password, "new_password": new_password}
        )
        return success

    def test_create_folder(self, name="Test Folder"):
        """Test folder creation"""
        success, response = self.run_test(
            "Create Folder",
            "POST",
            "folders",
            200,
            data={"name": name}
        )
        return response.get('id') if success else None

    def test_get_folders(self):
        """Test getting folders"""
        success, response = self.run_test(
            "Get Folders",
            "GET",
            "folders",
            200
        )
        return response if success else []

    def test_delete_folder(self, folder_id):
        """Test folder deletion"""
        success, response = self.run_test(
            "Delete Folder",
            "DELETE",
            f"folders/{folder_id}",
            200
        )
        return success

    def test_upload_video(self, title="Test Video", description="Test Description"):
        """Test video upload with a small test file"""
        # Create a small test file
        test_content = b"fake video content for testing"
        
        success, response = self.run_test(
            "Upload Video",
            "POST",
            "videos/upload",
            200,
            data={
                "title": title,
                "description": description
            },
            files={"file": ("test_video.mp4", test_content, "video/mp4")}
        )
        return response.get('video_id') if success else None

    def test_get_videos(self):
        """Test getting videos"""
        success, response = self.run_test(
            "Get Videos",
            "GET",
            "videos",
            200
        )
        return response if success else []

    def test_get_video(self, video_id):
        """Test getting single video"""
        success, response = self.run_test(
            "Get Single Video",
            "GET",
            f"videos/{video_id}",
            200
        )
        return response if success else None

    def test_update_video(self, video_id, title="Updated Title"):
        """Test video update"""
        success, response = self.run_test(
            "Update Video",
            "PATCH",
            f"videos/{video_id}?title={title}",
            200
        )
        return success

    def test_create_embed_settings(self, video_id):
        """Test embed settings creation"""
        success, response = self.run_test(
            "Create Embed Settings",
            "POST",
            "embed-settings",
            200,
            data={
                "video_id": video_id,
                "allowed_domains": ["example.com"],
                "player_color": "#ff0000",
                "show_controls": True,
                "autoplay": False,
                "loop": False
            }
        )
        return success

    def test_get_embed_settings(self, video_id):
        """Test getting embed settings"""
        success, response = self.run_test(
            "Get Embed Settings",
            "GET",
            f"embed-settings/{video_id}",
            200
        )
        return response if success else None

    def test_get_embed_code(self, video_id):
        """Test getting embed code"""
        success, response = self.run_test(
            "Get Embed Code",
            "GET",
            f"embed-code/{video_id}",
            200
        )
        return response.get('embed_code') if success else None

    def test_delete_video(self, video_id):
        """Test video deletion"""
        success, response = self.run_test(
            "Delete Video",
            "DELETE",
            f"videos/{video_id}",
            200
        )
        return success

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Video Hosting Service API Tests")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)

        # Test 1: Login with default credentials
        login_success, must_change_password = self.test_login()
        if not login_success:
            print("❌ Login failed, stopping tests")
            return False

        # Test 2: Change password if required
        if must_change_password:
            if not self.test_change_password():
                print("❌ Password change failed, stopping tests")
                return False
            
            # Login again with new password
            login_success, _ = self.test_login("admin", "NewSecurePass123!")
            if not login_success:
                print("❌ Login with new password failed, stopping tests")
                return False

        # Test 3: Folder management
        folder_id = self.test_create_folder("Test Folder")
        if folder_id:
            folders = self.test_get_folders()
            print(f"   Found {len(folders)} folders")

        # Test 4: Video upload and management
        video_id = self.test_upload_video("Test Video", "Test video description")
        if video_id:
            print(f"   Video uploaded with ID: {video_id}")
            
            # Wait a moment for processing to start
            time.sleep(2)
            
            # Get videos
            videos = self.test_get_videos()
            print(f"   Found {len(videos)} videos")
            
            # Get single video
            video_details = self.test_get_video(video_id)
            if video_details:
                print(f"   Video status: {video_details.get('processing_status', 'unknown')}")
            
            # Update video
            self.test_update_video(video_id, "Updated Test Video")
            
            # Test embed settings
            if self.test_create_embed_settings(video_id):
                embed_settings = self.test_get_embed_settings(video_id)
                if embed_settings:
                    print(f"   Embed settings created with color: {embed_settings.get('player_color')}")
                
                # Get embed code
                embed_code = self.test_get_embed_code(video_id)
                if embed_code:
                    print(f"   Embed code generated ({len(embed_code)} characters)")
            
            # Clean up - delete video
            self.test_delete_video(video_id)

        # Clean up - delete folder
        if folder_id:
            self.test_delete_folder(folder_id)

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = VideoHostingAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        all_passed = tester.print_summary()
        
        # Save results to file
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            "test_details": tester.test_results
        }
        
        with open("/app/backend_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())