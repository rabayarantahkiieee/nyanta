# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import os
import threading
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, MetaData, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import func

DB_URI = os.environ.get("DATABASE_URL", "sqlite:///bot_database.db")

# SQLAlchemy setup
Base = declarative_base()

# User status constants
USER_STATUS_ACTIVE = "active"
USER_STATUS_BLOCKED = "blocked"
USER_STATUS_DELETED = "deleted"

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
    status = Column(String(20), default=USER_STATUS_ACTIVE, nullable=False)
    is_blocked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

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
                
                # Check if status column exists, if not add it
                result = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'status'")
                if result.fetchone() is None:
                    print("[INFO] Adding status columns to users table...")
                    conn.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
                    conn.execute("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE")
                    conn.execute("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
                    conn.commit()
                    print("[INFO] Status columns added successfully")
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
    """
    Add or update user in database.
    This function is now more robust and handles username updates.
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if user is None:
            # Create new user
            new_user = User(
                user_id=user_id,
                username=username,
                status=USER_STATUS_ACTIVE,
                is_blocked=False,
                is_deleted=False
            )
            db.add(new_user)
            print(f"[INFO] New user added: {user_id} (@{username})")
        else:
            # Update existing user
            user.username = username
            user.status = USER_STATUS_ACTIVE  # Reactivate if was blocked
            user.is_blocked = False
            user.is_deleted = False
            user.last_seen = func.now()
            # Only print if username changed
            if user.username != username:
                print(f"[INFO] User updated: {user_id} (@{username})")
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Add user error: {e}")
        return False
    finally:
        db.close()

def update_user_status(user_id, status, is_blocked=None, is_deleted=None):
    """
    Update user status (active, blocked, deleted).
    Uses soft delete - marks as blocked/deleted instead of removing.
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.status = status
            if is_blocked is not None:
                user.is_blocked = is_blocked
            if is_deleted is not None:
                user.is_deleted = is_deleted
            if status == USER_STATUS_ACTIVE:
                user.is_blocked = False
                user.is_deleted = False
            user.last_seen = func.now()
            db.commit()
            print(f"[INFO] User status updated: {user_id} -> {status}")
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Update user status error: {e}")
        return False
    finally:
        db.close()

def delete_user(user_id, soft_delete=True):
    """
    Delete user from database.
    If soft_delete=True, marks as deleted instead of removing.
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            if soft_delete:
                # Soft delete - mark as deleted
                user.status = USER_STATUS_DELETED
                user.is_deleted = True
                user.is_blocked = False
                db.commit()
                print(f"[INFO] User soft-deleted: {user_id}")
            else:
                # Hard delete - remove from database
                db.delete(user)
                db.commit()
                print(f"[INFO] User hard-deleted: {user_id}")
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Delete user error: {e}")
        return False
    finally:
        db.close()

def mark_user_blocked(user_id):
    """
    Mark user as blocked (soft delete).
    """
    return update_user_status(user_id, USER_STATUS_BLOCKED, is_blocked=True, is_deleted=False)

def sync_user_activity(user_id, username):
    """
    Sync user activity - update last_seen and username if changed.
    Call this whenever user interacts with the bot.
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            # Update username if changed
            username_changed = user.username != username
            user.username = username
            user.last_seen = func.now()
            
            # Reactivate user if they were blocked/deleted
            if user.status != USER_STATUS_ACTIVE:
                user.status = USER_STATUS_ACTIVE
                user.is_blocked = False
                user.is_deleted = False
                print(f"[INFO] User reactivated: {user_id} (@{username})")
            
            db.commit()
            return username_changed
        else:
            # User doesn't exist, add them
            add_user(user_id, username)
            return True
    except Exception as e:
        db.rollback()
        print(f"Sync user activity error: {e}")
        return False
    finally:
        db.close()

async def full_userbase(include_inactive=False):
    """Get all users from database"""
    db = get_db()
    try:
        query = db.query(User)
        if not include_inactive:
            query = query.filter(User.status == USER_STATUS_ACTIVE)
        users = query.order_by(User.last_seen.desc()).all()
        # Convert to list of tuples for compatibility
        return [(user.user_id, user.username) for user in users]
    except Exception as e:
        print(f"Full userbase error: {e}")
        return []
    finally:
        db.close()

async def query_msg(active_only=True):
    """Get all user IDs for broadcasting"""
    db = get_db()
    try:
        query = db.query(User)
        if active_only:
            query = query.filter(User.status == USER_STATUS_ACTIVE)
        users = query.all()
        # Convert to list of tuples for compatibility
        return [(user.user_id,) for user in users]
    except Exception as e:
        print(f"Query message error: {e}")
        return []
    finally:
        db.close()

def get_user_count(include_inactive=False):
    """Get total user count"""
    db = get_db()
    try:
        query = db.query(User)
        if not include_inactive:
            query = query.filter(User.status == USER_STATUS_ACTIVE)
        count = query.count()
        return count
    except Exception as e:
        print(f"Get user count error: {e}")
        return 0
    finally:
        db.close()

def get_user_stats():
    """Get user statistics including active, blocked, deleted counts"""
    db = get_db()
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.status == USER_STATUS_ACTIVE).count()
        blocked_users = db.query(User).filter(User.status == USER_STATUS_BLOCKED).count()
        deleted_users = db.query(User).filter(User.status == USER_STATUS_DELETED).count()
        active_today = db.query(User).filter(
            User.status == USER_STATUS_ACTIVE,
            func.date(User.last_seen) == func.date(func.now())
        ).count()
        return {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'deleted_users': deleted_users,
            'active_today': active_today
        }
    except Exception as e:
        print(f"Get user stats error: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'blocked_users': 0,
            'deleted_users': 0,
            'active_today': 0
        }
    finally:
        db.close()

def update_user_subscription_status(user_id, username, is_subscribed=True):
    """Update user's subscription status in database"""
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            # Create new user if not exists
            user = User(
                user_id=user_id, 
                username=username,
                status=USER_STATUS_ACTIVE,
                is_blocked=False,
                is_deleted=False
            )
            db.add(user)
        else:
            # Update existing user
            user.username = username
            user.last_seen = func.now()
            if is_subscribed:
                user.status = USER_STATUS_ACTIVE
                user.is_blocked = False

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Update subscription status error: {e}")
    finally:
        db.close()

def get_user_by_id(user_id):
    """Get user by ID"""
    db = get_db()
    try:
        return db.query(User).filter(User.user_id == user_id).first()
    except Exception as e:
        print(f"Get user error: {e}")
        return None
    finally:
        db.close()

def cleanup_blocked_users(max_age_days=30):
    """
    Clean up old blocked/deleted users.
    Optionally hard delete users who have been blocked/deleted for more than max_age_days.
    """
    from datetime import timedelta
    db = get_db()
    try:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        # Get old blocked/deleted users
        old_users = db.query(User).filter(
            User.status.in_([USER_STATUS_BLOCKED, USER_STATUS_DELETED]),
            User.last_seen < cutoff_date
        ).all()
        
        count = len(old_users)
        for user in old_users:
            db.delete(user)
        
        db.commit()
        print(f"[INFO] Cleaned up {count} old blocked/deleted users")
        return count
    except Exception as e:
        db.rollback()
        print(f"Cleanup error: {e}")
        return 0
    finally:
        db.close()
