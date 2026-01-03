#!/usr/bin/env python
"""Reset database and create initial data"""

import os
import sys
from app import app, db
from models import User, UserRole
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    """Drop all tables and recreate them"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        print("Creating default test user...")
        # Create a test user with 'user' role
        test_user = User(
            username='demo',
            email='demo@example.com',
            role=UserRole.USER.value
        )
        test_user.set_password('demo1234')
        db.session.add(test_user)
        
        # Create a test admin
        admin_user = User(
            username='admin',
            email='admin@example.com',
            role=UserRole.ADMIN.value
        )
        admin_pass = os.environ.get('ADMIN_PASSWORD')
        if not admin_pass:
            print("❌ ERROR: 'ADMIN_PASSWORD' variable cannot be found in .env file!")
            print("   Please copy .env.example to make the .env file and fill the password.")
            sys.exit(1)
        admin_user.set_password(admin_pass)
        db.session.add(admin_user)
        
        # Create a test employee
        employee_user = User(
            username='employee',
            email='employee@example.com',
            role=UserRole.EMPLOYEE.value
        )
        employee_pass = os.environ.get('EMPLOYEE_PASSWORD')
        if not employee_pass:
            print("❌ ERROR: 'EMPLOYEE_PASSWORD' variable cannot be found in .env file!")
            print("   Please copy .env.example to make the .env file and fill the password.")
            sys.exit(1)
        employee_user.set_password(employee_pass)
        db.session.add(employee_user)
        
        db.session.commit()
        
        print("✅ Database reset successfully!")
        print("\nDefault test users created:")
        print("  👤 User: demo / demo1234")
        print("  🔐 Admin: admin / admin1234")
        print("  👨‍💼 Employee: employee / employee1234")

if __name__ == '__main__':
    reset_database()
