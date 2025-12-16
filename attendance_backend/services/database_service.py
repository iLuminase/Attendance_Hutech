"""
Service xử lý kết nối database MySQL
Tách riêng logic database để dễ quản lý
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.database import DB_URL, Base
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        """Khởi tạo database service"""
        self.engine = None
        self.SessionLocal = None
        self.setup_connection()

    def setup_connection(self):
        """Thiết lập kết nối database"""
        try:
            # Tạo engine với connection pooling
            self.engine = create_engine(
                DB_URL,
                pool_size=10,          # Số connection trong pool
                max_overflow=20,       # Số connection tối đa
                pool_recycle=3600,     # Recycle connection sau 1h
                pool_pre_ping=True,    # Kiểm tra connection trước khi dùng
                echo=True              # Log SQL queries để debug
            )

            # Tạo session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logger.info("✅ Database connection established successfully")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Kiểm tra kết nối database"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection test passed")
                return True
        except OperationalError as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

    def create_tables(self):
        """Tạo tất cả bảng từ models"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ All tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise

    def get_db(self) -> Session:
        """Dependency để lấy database session"""
        db = self.SessionLocal()
        try:
            yield db
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def health_check(self) -> dict:
        """Kiểm tra tình trạng database"""
        try:
            with self.engine.connect() as conn:
                # Test basic query
                result = conn.execute(text("SELECT VERSION()"))
                mysql_version = result.fetchone()[0]

                # Check tables
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]

                return {
                    "status": "healthy",
                    "mysql_version": mysql_version,
                    "tables_count": len(tables),
                    "tables": tables
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Singleton instance
db_service = DatabaseService()
