#!/usr/bin/env python3
"""
Create initial admin user script.

This script creates the first admin user for the Healthcare AI Assistant.
It prompts for email and password, validates inputs, and creates a user
with is_admin=True.

Requirements: 21.1, 21.2

Usage:
    python scripts/create_admin_user.py
    
    Or with command-line arguments:
    python scripts/create_admin_user.py --email admin@example.com --password SecurePass123!
"""

import sys
import os
import argparse
import getpass
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.services.user_service import UserService
from src.utils.config import settings


def prompt_for_credentials():
    """
    Prompt user for admin email and password.
    
    Returns:
        tuple: (email, password)
    """
    print("\n" + "=" * 60)
    print("Create Initial Admin User")
    print("=" * 60)
    print()
    
    # Prompt for email
    email = input("Enter admin email: ").strip()
    
    # Prompt for password (hidden input)
    password = getpass.getpass("Enter admin password: ")
    confirm_password = getpass.getpass("Confirm admin password: ")
    
    # Verify passwords match
    if password != confirm_password:
        print("\n❌ Error: Passwords do not match")
        sys.exit(1)
    
    return email, password


def create_admin_user(email: str, password: str):
    """
    Create an admin user with the provided credentials.
    
    Args:
        email: Admin email address
        password: Admin password
        
    Returns:
        User: The created admin user
        
    Raises:
        ValueError: If validation fails or user already exists
    """
    # Create database engine and session
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create user service
        user_service = UserService(db)
        
        # Create admin user
        admin = user_service.create_user(
            email=email,
            password=password,
            is_admin=True
        )
        
        return admin
    finally:
        db.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Create initial admin user for Healthcare AI Assistant"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Admin email address (will prompt if not provided)"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Admin password (will prompt if not provided, recommended for security)"
    )
    
    args = parser.parse_args()
    
    # Get credentials from arguments or prompt
    if args.email and args.password:
        email = args.email
        password = args.password
        print("\n" + "=" * 60)
        print("Create Initial Admin User")
        print("=" * 60)
        print()
    else:
        email, password = prompt_for_credentials()
    
    # Create admin user
    try:
        print("\nCreating admin user...")
        admin = create_admin_user(email, password)
        
        print("\n" + "=" * 60)
        print("✅ Success!")
        print("=" * 60)
        print(f"\nAdmin user created successfully:")
        print(f"  Email: {admin.email}")
        print(f"  User ID: {admin.id}")
        print(f"  Admin: {admin.is_admin}")
        print(f"  Created: {admin.created_at}")
        print()
        
    except ValueError as e:
        print("\n" + "=" * 60)
        print("❌ Error")
        print("=" * 60)
        print(f"\n{str(e)}")
        print()
        print("Common issues:")
        print("  • Email format is invalid")
        print("  • Email is already registered")
        print("  • Password does not meet strength requirements:")
        print("    - Minimum 8 characters")
        print("    - At least one uppercase letter")
        print("    - At least one lowercase letter")
        print("    - At least one number")
        print("    - At least one special character")
        print()
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Unexpected Error")
        print("=" * 60)
        print(f"\n{str(e)}")
        print()
        print("Please ensure:")
        print("  • Database is accessible")
        print("  • Database migrations have been run")
        print("  • Environment variables are configured correctly")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
