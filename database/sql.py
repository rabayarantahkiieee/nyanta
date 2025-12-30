# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import os
import threading
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import func

DB_URI = os.environ.get("DATABASE_URL", "sqlite:///bot_database.db")

# SQLAlchemy setup
Base = declarative_base()

# Handle database URL for different providers
if DB_URI.startswith("postgres://"):
    DB_URI = DB_URI.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate settings
if "postgresql" in DB_URI:
    engine = create_engine(
        DB_URI,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )
else:
    # SQLite settings
    engine = create_engine(
        DB_URI,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"check_same_thread": False}
    )

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Create tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("[INFO] Database tables created successfully")

    # Handle database migration for user_id column
    if "postgresql" in DB_URI:
        try:
            with engine.connect() as conn:
                # Check if user_id column is still INTEGER and needs to be changed to BIGINT
                result = conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'user_id'")
                row = result.fetchone()
                if row and row[0] == 'integer':
                    print("[INFO] Migrating user_id column from INTEGER to BIGINT...")
                    conn.execute("ALTER TABLE users ALTER COLUMN user_id TYPE BIGINT")
                    conn.commit()
                    print("[INFO] Database migration completed successfully")
        except Exception as migration_e:
            print(f"[WARNING] Database migration failed: {migration_e}")
            # Continue execution

except Exception as e:
    print(f"[WARNING] Database table creation failed: {e}")
    # Continue execution even if table creation fails

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def add_user(user_id, username):
    """Add user to database"""
    db = get_db()
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            # Create new user
            new_user = User(user_id=user_id, username=username)
            db.add(new_user)
        else:
            # Update existing user
            user.username = username
            user.last_seen = func.now()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Add user error: {e}")
    finally:
        db.close()

def delete_user(user_id):
    """Delete user from database"""
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Delete user error: {e}")
    finally:
        db.close()

async def full_userbase():
    """Get all users from database"""
    db = get_db()
    try:
        users = db.query(User).order_by(User.first_seen.desc()).all()
        # Convert to list of tuples for compatibility
        return [(user.user_id, user.username) for user in users]
    except Exception as e:
        print(f"Full userbase error: {e}")
        return []
    finally:
        db.close()

async def query_msg():
    """Get all user IDs for broadcasting"""
    db = get_db()
    try:
        users = db.query(User).all()
        # Convert to list of tuples for compatibility
        return [(user.user_id,) for user in users]
    except Exception as e:
        print(f"Query message error: {e}")
        return []
    finally:
        db.close()

def get_user_count():
    """Get total user count"""
    db = get_db()
    try:
        count = db.query(User).count()
        return count
    except Exception as e:
        print(f"Get user count error: {e}")
        return 0
    finally:
        db.close()

def get_user_stats():
    """Get user statistics"""
    db = get_db()
    try:
        total_users = db.query(User).count()
        active_today = db.query(User).filter(
            func.date(User.last_seen) == func.date(func.now())
        ).count()
        return {
            'total_users': total_users,
            'active_today': active_today
        }
    except Exception as e:
        print(f"Get user stats error: {e}")
        return {'total_users': 0, 'active_today': 0}
    finally:
        db.close()

def update_user_subscription_status(user_id, username, is_subscribed=True):
    """Update user's subscription status in database"""
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            # Create new user if not exists
            user = User(user_id=user_id, username=username)
            db.add(user)
        else:
            # Update existing user
            user.username = username
            user.last_seen = func.now()

        # Here we could add a subscription_status field if needed
        # For now, we just ensure the user is in database when they subscribe
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Update subscription status error: {e}")
    finally:
        db.close()