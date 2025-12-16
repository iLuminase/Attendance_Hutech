"""
Demo script để test MySQL connection và API
Chạy script này để kiểm tra toàn bộ hệ thống
"""
import requests
import json
from setup_database import test_connection
import time

def test_mysql_connection():
    """Test kết nối MySQL trực tiếp"""
    print("🔍 Testing MySQL connection...")
    try:
        test_connection()
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def test_api_endpoints():
    """Test các API endpoints"""
    base_url = "http://127.0.0.1:8000"

    print("\n🌐 Testing API endpoints...")

    try:
        # Test health check
        print("  📍 Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"     Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"     API: {health_data['api_status']}")
            print(f"     Database: {health_data['database']['status']}")
            if 'mysql_version' in health_data['database']:
                print(f"     MySQL Version: {health_data['database']['mysql_version']}")

        # Test create class
        print("\n  📚 Testing create class...")
        class_data = {
            "class_id": "CS101",
            "class_name": "Lập trình Python",
            "subject_name": "Computer Science",
            "lecturer_name": "Thầy Nguyễn Văn A"
        }
        response = requests.post(f"{base_url}/classes/", json=class_data, timeout=5)
        print(f"     Status: {response.status_code}")
        print(f"     Response: {response.json()}")

        # Test create student
        print("\n  👨‍🎓 Testing create student...")
        student_data = {
            "student_id": "2021603080001",
            "full_name": "Nguyễn Văn B",
            "class_id": "CS101"
        }
        response = requests.post(f"{base_url}/students/", json=student_data, timeout=5)
        print(f"     Status: {response.status_code}")
        print(f"     Response: {response.json()}")

        # Test get all students
        print("\n  📋 Testing get all students...")
        response = requests.get(f"{base_url}/students/", timeout=5)
        print(f"     Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"     Total students: {data['total']}")

        # Test get all classes
        print("\n  📚 Testing get all classes...")
        response = requests.get(f"{base_url}/classes/", timeout=5)
        print(f"     Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"     Total classes: {data['total']}")

        return True

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server!")
        print("💡 Make sure to start the server with:")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main demo function"""
    print("🎯 HUTECH Attendance System - MySQL Connection Demo")
    print("=" * 60)

    # Step 1: Test MySQL connection
    mysql_ok = test_mysql_connection()

    if not mysql_ok:
        print("\n❌ MySQL connection failed!")
        print("💡 Troubleshooting steps:")
        print("   1. Check MySQL service is running")
        print("   2. Verify credentials in .env file")
        print("   3. Run: python setup_database.py")
        return

    # Step 2: Wait for user to start server
    print("\n🚀 MySQL connection successful!")
    print("Now start the FastAPI server in another terminal:")
    print("   python -m uvicorn app.main:app --reload")
    print("\nWhen the server is running, press Enter to continue...")
    input()

    # Step 3: Test API endpoints
    api_ok = test_api_endpoints()

    if api_ok:
        print("\n✅ All tests passed!")
        print("🎉 Your HUTECH Attendance System is ready!")
        print("\n📖 Access API documentation at: http://127.0.0.1:8000/docs")
    else:
        print("\n❌ Some API tests failed!")
        print("💡 Check the server logs for more details")

if __name__ == "__main__":
    main()
