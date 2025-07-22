#!/usr/bin/env python3
"""
LSP tables initialization script
Adds columns to existing users table and creates user_scores table
"""
import psycopg2
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.configs.global_config import POSTGRES_CONFIG


def init_lsp_tables():
    """Initialize LSP specific tables and columns"""
    print("Starting LSP tables initialization...")
    print(f"Database: {POSTGRES_CONFIG.dbname}")
    print(f"Host: {POSTGRES_CONFIG.host}:{POSTGRES_CONFIG.port}")
    
    # Read SQL script
    sql_file = Path(__file__).parent / "create_lsp_tables.sql"
    if not sql_file.exists():
        print(f"Error: SQL script not found: {sql_file}")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=POSTGRES_CONFIG.dbname,
            user=POSTGRES_CONFIG.user,
            password=POSTGRES_CONFIG.pwd.get_secret_value(),
            host=POSTGRES_CONFIG.host,
            port=POSTGRES_CONFIG.port
        )
        
        with conn.cursor() as cursor:
            # Check if users table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """)
            
            if not cursor.fetchone()[0]:
                print("Error: users table does not exist!")
                print("Please ensure the users table is created in your database first.")
                return False
            
            # Execute SQL script
            print("\nExecuting LSP table modifications...")
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                cursor.execute(sql_content)
            
            conn.commit()
            print("✅ LSP tables created successfully!")
            
            # Verify modifications
            print("\nVerifying table structure...")
            
            # Check users table columns
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('level', 'total_points')
                ORDER BY column_name
            """)
            
            user_columns = cursor.fetchall()
            if len(user_columns) == 2:
                print("\n✅ Users table modifications:")
                for col in user_columns:
                    print(f"  - {col[0]}: {col[1]} (default: {col[2]})")
            else:
                print("⚠️  Warning: Not all columns were added to users table")
            
            # Check user_scores table
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'user_scores'
            """)
            
            if cursor.fetchone()[0] > 0:
                # Get column count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_scores'
                """)
                col_count = cursor.fetchone()[0]
                
                # Get record count
                cursor.execute("SELECT COUNT(*) FROM user_scores")
                row_count = cursor.fetchone()[0]
                
                print(f"\n✅ user_scores table: {col_count} columns, {row_count} records")
                
                # Show indexes
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'user_scores' 
                    ORDER BY indexname
                """)
                indexes = cursor.fetchall()
                print("\nIndexes created:")
                for idx in indexes:
                    print(f"  - {idx[0]}")
            else:
                print("❌ user_scores table was not created")
            
            return True
            
    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def check_existing_structure():
    """Check existing database structure"""
    print("\nChecking existing database structure...")
    
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_CONFIG.dbname,
            user=POSTGRES_CONFIG.user,
            password=POSTGRES_CONFIG.pwd.get_secret_value(),
            host=POSTGRES_CONFIG.host,
            port=POSTGRES_CONFIG.port
        )
        
        with conn.cursor() as cursor:
            # Check users table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            
            print("\nExisting users table structure:")
            columns = cursor.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  - {col[0]}: {col[1]} {nullable}{default}")
            
            # Check if LSP columns already exist
            lsp_columns = [col[0] for col in columns if col[0] in ('level', 'total_points')]
            if lsp_columns:
                print(f"\n⚠️  Warning: LSP columns already exist: {', '.join(lsp_columns)}")
            
    except Exception as e:
        print(f"Error checking structure: {e}")
    finally:
        if conn:
            conn.close()


def main():
    """Main function"""
    print("LSP Score System - Table Initialization")
    print("=" * 50)
    
    # Check existing structure
    check_existing_structure()
    
    # Confirm before proceeding
    print("\nThis script will:")
    print("1. Add 'level' and 'total_points' columns to the existing users table")
    print("2. Create a new user_scores table")
    print("3. Create necessary indexes")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Initialize tables
    if init_lsp_tables():
        print("\n🎉 LSP tables initialization completed!")
        print("\nNext steps:")
        print("1. Start API service: python start_server.py")
        print("2. Access documentation: http://localhost:8000/lsp/docs")
    else:
        print("\nInitialization failed, please check error messages")
        sys.exit(1)


if __name__ == "__main__":
    main()