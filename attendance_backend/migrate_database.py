#!/usr/bin/env python3
"""
Migration script để cập nhật schema database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.database import DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate database schema"""
    try:
        engine = create_engine(DB_URL)
        
        with engine.connect() as conn:
            logger.info("🔨 Starting database migration...")
            
            # Kiểm tra cấu trúc hiện tại
            result = conn.execute(text("DESCRIBE students"))
            current_columns = {row[0]: row[1] for row in result}
            logger.info(f"Current students table columns: {list(current_columns.keys())}")
            
            # Migration steps
            migrations = []

            # 1. Rename full_name to name if needed
            if 'full_name' in current_columns and 'name' not in current_columns:
                migrations.append("ALTER TABLE students CHANGE full_name name VARCHAR(100) NOT NULL")
            
            # 2. Add email column
            if 'email' not in current_columns:
                migrations.append("ALTER TABLE students ADD COLUMN email VARCHAR(100) UNIQUE AFTER name")
            
            # 3. Add phone column
            if 'phone' not in current_columns:
                migrations.append("ALTER TABLE students ADD COLUMN phone VARCHAR(15) AFTER email")
            
            # 5. Change class_id to VARCHAR(20)
            if 'class_id' in current_columns and 'varchar' not in str(current_columns['class_id']).lower():
                migrations.append("ALTER TABLE students MODIFY COLUMN class_id VARCHAR(20)")
            
            # 4. Add face_image
            if 'face_image' not in current_columns:
                migrations.append("ALTER TABLE students ADD COLUMN face_image LONGBLOB AFTER face_encoding")

            # 5. Add face_encoding_version
            if 'face_encoding_version' not in current_columns:
                migrations.append("ALTER TABLE students ADD COLUMN face_encoding_version VARCHAR(10) DEFAULT '1.0' AFTER face_encoding")
            
            # 6. Add updated_at
            if 'updated_at' not in current_columns:
                migrations.append("ALTER TABLE students ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at")
            
            # 8. Add indexes
            try:
                conn.execute(text("CREATE UNIQUE INDEX idx_student_id ON students(student_id)"))
                logger.info("✅ Created index on student_id")
            except:
                logger.info("ℹ️  Index on student_id already exists")
            
            try:
                conn.execute(text("CREATE INDEX idx_class_id ON students(class_id)"))
                logger.info("✅ Created index on class_id")
            except:
                logger.info("ℹ️  Index on class_id already exists")
            
            try:
                conn.execute(text("CREATE UNIQUE INDEX idx_email ON students(email)"))
                logger.info("✅ Created index on email")
            except:
                logger.info("ℹ️  Index on email already exists")
            
            # Execute migrations
            for i, migration in enumerate(migrations, 1):
                try:
                    logger.info(f"🔧 Executing migration {i}/{len(migrations)}: {migration}")
                    conn.execute(text(migration))
                    conn.commit()
                    logger.info(f"✅ Migration {i} completed")
                except Exception as e:
                    logger.error(f"❌ Migration {i} failed: {e}")
                    conn.rollback()
            
            # Verify final structure
            logger.info("🔍 Verifying final structure...")
            result = conn.execute(text("DESCRIBE students"))
            final_columns = [row[0] for row in result]
            logger.info(f"Final students table columns: {final_columns}")
            
            # Check if all required columns exist
            required_columns = ['student_id', 'name', 'email', 'phone', 'class_id', 'face_encoding', 'face_image', 'face_encoding_version', 'created_at', 'updated_at']
            missing = [col for col in required_columns if col not in final_columns]
            
            if missing:
                logger.warning(f"⚠️  Still missing columns: {missing}")
            else:
                logger.info("✅ All required columns present")
                
            logger.info("🎉 Database migration completed!")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_database()