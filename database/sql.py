# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, MetaData, Table, Boolean, text
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
    language = Column(String(5), nullable=True)

DEFAULT_LANGUAGE = "id"
SUPPORTED_LANGUAGES = ("id", "en")

class BotSetting(Base):
    """Generic key/value store for global bot configuration."""
    __tablename__ = "bot_settings"

    key = Column(String(64), primary_key=True)
    value = Column(String, nullable=True)

class UserCustomLimit(Base):
    """Per-user override of the global daily download limit."""
    __tablename__ = "user_custom_limits"

    user_id = Column(BigInteger, primary_key=True)
    daily_limit = Column(Integer, nullable=False)

class UserDailyDownload(Base):
    """Tracks how many downloads a user made on a given date."""
    __tablename__ = "user_daily_downloads"

    user_id = Column(BigInteger, primary_key=True)
    date = Column(String(10), nullable=False)
    download_count = Column(Integer, default=0, nullable=False)

class UserVerification(Base):
    """Tracks how long a user's in-bot anti-leech verification stays valid."""
    __tablename__ = "user_verifications"

    user_id = Column(BigInteger, primary_key=True)
    verified_until = Column(DateTime(timezone=True), nullable=False)

class CustomButton(Base):
    """Admin-configured buttons shown alongside delivered files."""
    __tablename__ = "custom_buttons"

    button_id = Column(String(32), primary_key=True)
    text = Column(String, nullable=False)
    url = Column(String, nullable=False)

class CustomMessage(Base):
    """Admin-configured messages for situations like welcome/error/limit/protected."""
    __tablename__ = "custom_messages"

    msg_type = Column(String(32), primary_key=True)
    content_type = Column(String(20), default="text", nullable=False)
    content = Column(String, nullable=True)
    media_id = Column(String, nullable=True)
    media_type = Column(String(20), nullable=True)
    buttons_json = Column(String, nullable=True)

class ProtectedFile(Base):
    """Files flagged as protected via /addkonten."""
    __tablename__ = "protected_files"

    message_id = Column(BigInteger, primary_key=True)

class ContentDownloadLimit(Base):
    """Per-file remaining download count, set independently via /limitkonten."""
    __tablename__ = "content_download_limits"

    message_id = Column(BigInteger, primary_key=True)
    download_limit = Column(Integer, nullable=False)

class FileIndex(Base):
    """Searchable index of files stored in the database channel."""
    __tablename__ = "file_index"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(BigInteger, unique=True, index=True, nullable=False)
    file_name = Column(String, nullable=False, index=True)
    file_type = Column(String(20), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    caption = Column(String, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

# Create tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("[INFO] Database tables created successfully")

    # Handle database migration for user_id column
    if "postgresql" in DB_URI:
        try:
            with engine.connect() as conn:
                # Check if user_id column is still INTEGER and needs to be changed to BIGINT
                result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'user_id'"))
                row = result.fetchone()
                if row and row[0] == 'integer':
                    print("[INFO] Migrating user_id column from INTEGER to BIGINT...")
                    conn.execute(text("ALTER TABLE users ALTER COLUMN user_id TYPE BIGINT"))
                    conn.commit()
                    print("[INFO] Database migration completed successfully")

                # Check if status column exists, if not add it
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'status'"))
                if result.fetchone() is None:
                    print("[INFO] Adding status columns to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE"))
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                    print("[INFO] Status columns added successfully")

                # Check if language column exists, if not add it
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'language'"))
                if result.fetchone() is None:
                    print("[INFO] Adding language column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR(5)"))
                    conn.commit()
                    print("[INFO] Language column added successfully")
        except Exception as migration_e:
            print(f"[WARNING] Database migration failed: {migration_e}")
            # Continue execution
    else:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(users)"))
                existing_columns = {row[1] for row in result.fetchall()}
                if "language" not in existing_columns:
                    print("[INFO] Adding language column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR(5)"))
                    conn.commit()
                    print("[INFO] Language column added successfully")
        except Exception as migration_e:
            print(f"[WARNING] SQLite database migration failed: {migration_e}")
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


def get_user_join_info(user_id):
    """
    Get user join information for placeholder replacement.
    Returns dict with first_seen date/time information.
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user and user.first_seen:
            return {
                'first_seen': user.first_seen,
                'join_date': user.first_seen.strftime('%d/%m/%Y'),
                'join_time': user.first_seen.strftime('%H:%M:%S'),
                'join_weekday': get_indonesian_weekday(user.first_seen),
                'join_iso': user.first_seen.isoformat()
            }
        else:
            # Return current datetime if user not found or no first_seen
            now = datetime.now()
            return {
                'first_seen': now,
                'join_date': now.strftime('%d/%m/%Y'),
                'join_time': now.strftime('%H:%M:%S'),
                'join_weekday': get_indonesian_weekday(now),
                'join_iso': now.isoformat()
            }
    except Exception as e:
        print(f"Get user join info error: {e}")
        now = datetime.now()
        return {
            'first_seen': now,
            'join_date': now.strftime('%d/%m/%Y'),
            'join_time': now.strftime('%H:%M:%S'),
            'join_weekday': get_indonesian_weekday(now),
            'join_iso': now.isoformat()
        }
    finally:
        db.close()


def get_indonesian_weekday(dt):
    """
    Get Indonesian weekday name from datetime object.
    """
    days = {
        0: 'Senin',
        1: 'Selasa',
        2: 'Rabu',
        3: 'Kamis',
        4: 'Jumat',
        5: 'Sabtu',
        6: 'Minggu'
    }
    return days.get(dt.weekday(), 'Unknown')

DEFAULT_DAILY_LIMIT = 2
DAILY_LIMIT_SETTING_KEY = "daily_download_limit"


def get_setting(key, default=None):
    """Get a global bot setting value (always returned as string, or default)."""
    db = get_db()
    try:
        row = db.query(BotSetting).filter(BotSetting.key == key).first()
        return row.value if row else default
    except Exception as e:
        print(f"Get setting error: {e}")
        return default
    finally:
        db.close()


def set_setting(key, value):
    """Set a global bot setting value."""
    db = get_db()
    try:
        row = db.query(BotSetting).filter(BotSetting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(BotSetting(key=key, value=str(value)))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Set setting error: {e}")
        return False
    finally:
        db.close()


def get_daily_limit_config():
    """Get the global daily download limit."""
    value = get_setting(DAILY_LIMIT_SETTING_KEY)
    try:
        return int(value) if value is not None else DEFAULT_DAILY_LIMIT
    except (TypeError, ValueError):
        return DEFAULT_DAILY_LIMIT


def set_daily_limit_config(new_limit):
    """Set the global daily download limit."""
    return set_setting(DAILY_LIMIT_SETTING_KEY, new_limit)


def get_user_custom_limit_db(user_id):
    """Get a user's custom daily limit, or None if not set."""
    db = get_db()
    try:
        row = db.query(UserCustomLimit).filter(UserCustomLimit.user_id == user_id).first()
        return row.daily_limit if row else None
    except Exception as e:
        print(f"Get user custom limit error: {e}")
        return None
    finally:
        db.close()


def set_user_custom_limit_db(user_id, limit):
    """Set a user's custom daily limit."""
    db = get_db()
    try:
        row = db.query(UserCustomLimit).filter(UserCustomLimit.user_id == user_id).first()
        if row:
            row.daily_limit = limit
        else:
            db.add(UserCustomLimit(user_id=user_id, daily_limit=limit))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Set user custom limit error: {e}")
        return False
    finally:
        db.close()


def delete_user_custom_limit_db(user_id):
    """Delete a user's custom daily limit. Returns True if a row was removed."""
    db = get_db()
    try:
        row = db.query(UserCustomLimit).filter(UserCustomLimit.user_id == user_id).first()
        if row:
            db.delete(row)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Delete user custom limit error: {e}")
        return False
    finally:
        db.close()


def get_all_user_custom_limits_db():
    """Get all users with a custom daily limit as {user_id_str: limit}."""
    db = get_db()
    try:
        rows = db.query(UserCustomLimit).all()
        return {str(r.user_id): r.daily_limit for r in rows}
    except Exception as e:
        print(f"Get all user custom limits error: {e}")
        return {}
    finally:
        db.close()


def try_consume_daily_download(user_id, today, daily_limit):
    """
    Atomically check-and-increment today's download counter for a user,
    resetting the counter first when the stored date differs from `today`.
    Returns True if the download is allowed (counter incremented), False if the
    daily limit has already been reached.
    """
    db = get_db()
    try:
        row = db.query(UserDailyDownload).filter(UserDailyDownload.user_id == user_id).first()
        if row is None:
            row = UserDailyDownload(user_id=user_id, date=today, download_count=0)
            db.add(row)
        elif row.date != today:
            row.date = today
            row.download_count = 0

        if row.download_count >= daily_limit:
            db.commit()
            return False

        row.download_count += 1
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Try consume daily download error: {e}")
        return False
    finally:
        db.close()


def get_daily_download_count(user_id, today):
    """Get today's download count for a user without incrementing it."""
    db = get_db()
    try:
        row = db.query(UserDailyDownload).filter(UserDailyDownload.user_id == user_id).first()
        if row is None or row.date != today:
            return 0
        return row.download_count
    except Exception as e:
        print(f"Get daily download count error: {e}")
        return 0
    finally:
        db.close()


def reset_all_daily_downloads(today):
    """Reset every user's daily download counter (admin function)."""
    db = get_db()
    try:
        db.query(UserDailyDownload).update({
            UserDailyDownload.download_count: 0,
            UserDailyDownload.date: today,
        })
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Reset all daily downloads error: {e}")
        return False
    finally:
        db.close()


def get_all_daily_downloads(today):
    """Get all users' download rows relevant to `today` as list of dicts."""
    db = get_db()
    try:
        rows = db.query(UserDailyDownload).all()
        result = []
        for row in rows:
            count = row.download_count if row.date == today else 0
            result.append({"user_id": row.user_id, "today_downloads": count})
        return result
    except Exception as e:
        print(f"Get all daily downloads error: {e}")
        return []
    finally:
        db.close()


def add_file_to_index(message_id, file_name, file_type=None, file_size=None, caption=None):
    """Add or update a file's entry in the searchable file index."""
    if not file_name:
        return False
    db = get_db()
    try:
        row = db.query(FileIndex).filter(FileIndex.message_id == message_id).first()
        if row:
            row.file_name = file_name
            row.file_type = file_type
            row.file_size = file_size
            row.caption = caption
        else:
            db.add(FileIndex(
                message_id=message_id,
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                caption=caption,
            ))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Add file to index error: {e}")
        return False
    finally:
        db.close()


def search_file_index(keyword, limit=20):
    """Search indexed files by (case-insensitive) filename substring."""
    db = get_db()
    try:
        pattern = f"%{keyword}%"
        rows = (
            db.query(FileIndex)
            .filter(FileIndex.file_name.ilike(pattern))
            .order_by(FileIndex.added_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "message_id": r.message_id,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "file_size": r.file_size,
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Search file index error: {e}")
        return []
    finally:
        db.close()


def get_file_index_count():
    """Get total number of indexed files."""
    db = get_db()
    try:
        return db.query(FileIndex).count()
    except Exception as e:
        print(f"Get file index count error: {e}")
        return 0
    finally:
        db.close()


VERIFICATION_ENABLED_KEY = "verification_enabled"
VERIFICATION_DELAY_SECONDS_KEY = "verification_delay_seconds"
VERIFICATION_VALID_HOURS_KEY = "verification_valid_hours"
DEFAULT_VERIFICATION_DELAY_SECONDS = 10
DEFAULT_VERIFICATION_VALID_HOURS = 24


def is_verification_enabled():
    """Whether the in-bot anti-leech verification gate is active."""
    return get_setting(VERIFICATION_ENABLED_KEY, "0") == "1"


def set_verification_enabled(enabled):
    return set_setting(VERIFICATION_ENABLED_KEY, "1" if enabled else "0")


def get_verification_delay_seconds():
    value = get_setting(VERIFICATION_DELAY_SECONDS_KEY)
    try:
        return int(value) if value is not None else DEFAULT_VERIFICATION_DELAY_SECONDS
    except (TypeError, ValueError):
        return DEFAULT_VERIFICATION_DELAY_SECONDS


def set_verification_delay_seconds(seconds):
    return set_setting(VERIFICATION_DELAY_SECONDS_KEY, seconds)


def get_verification_valid_hours():
    value = get_setting(VERIFICATION_VALID_HOURS_KEY)
    try:
        return int(value) if value is not None else DEFAULT_VERIFICATION_VALID_HOURS
    except (TypeError, ValueError):
        return DEFAULT_VERIFICATION_VALID_HOURS


def set_verification_valid_hours(hours):
    return set_setting(VERIFICATION_VALID_HOURS_KEY, hours)


def is_user_verified(user_id):
    """Whether the user currently has a non-expired verification."""
    db = get_db()
    try:
        row = db.query(UserVerification).filter(UserVerification.user_id == user_id).first()
        if not row:
            return False
        expires_at = row.verified_until
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires_at
    except Exception as e:
        print(f"Is user verified error: {e}")
        return False
    finally:
        db.close()


def set_user_verified(user_id, hours=None):
    """Mark a user as verified for `hours` (defaults to the configured value)."""
    if hours is None:
        hours = get_verification_valid_hours()
    db = get_db()
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        row = db.query(UserVerification).filter(UserVerification.user_id == user_id).first()
        if row:
            row.verified_until = expires_at
        else:
            db.add(UserVerification(user_id=user_id, verified_until=expires_at))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Set user verified error: {e}")
        return False
    finally:
        db.close()


def get_user_language(user_id):
    """Get a user's preferred language code, or None if not set."""
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        return user.language if user and user.language in SUPPORTED_LANGUAGES else None
    except Exception as e:
        print(f"Get user language error: {e}")
        return None
    finally:
        db.close()


def set_user_language(user_id, language):
    """Set a user's preferred language code."""
    if language not in SUPPORTED_LANGUAGES:
        return False
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.language = language
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Set user language error: {e}")
        return False
    finally:
        db.close()


# =============================================================================
# CUSTOM BUTTONS
# =============================================================================

def get_all_custom_buttons():
    """Get all custom buttons as {button_id: {"text":..., "url":...}}."""
    db = get_db()
    try:
        rows = db.query(CustomButton).all()
        return {r.button_id: {"text": r.text, "url": r.url} for r in rows}
    except Exception as e:
        print(f"Get all custom buttons error: {e}")
        return {}
    finally:
        db.close()


def sync_custom_buttons(buttons):
    """Replace all custom buttons with the given {button_id: {"text","url"}} dict."""
    db = get_db()
    try:
        existing = {r.button_id: r for r in db.query(CustomButton).all()}
        for button_id, row in list(existing.items()):
            if button_id not in buttons:
                db.delete(row)
        for button_id, data in buttons.items():
            if button_id in existing:
                existing[button_id].text = data.get("text", "")
                existing[button_id].url = data.get("url", "")
            else:
                db.add(CustomButton(button_id=button_id, text=data.get("text", ""), url=data.get("url", "")))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Sync custom buttons error: {e}")
        return False
    finally:
        db.close()


DEFAULT_BUTTONS_ENABLED_KEY = "default_buttons_enabled"


def get_default_buttons_enabled():
    """Whether the channel's own file buttons are shown alongside custom ones."""
    return get_setting(DEFAULT_BUTTONS_ENABLED_KEY, "1") == "1"


def set_default_buttons_enabled(enabled):
    return set_setting(DEFAULT_BUTTONS_ENABLED_KEY, "1" if enabled else "0")


# =============================================================================
# CUSTOM MESSAGES
# =============================================================================

def _custom_message_row_to_dict(row):
    return {
        "type": row.content_type,
        "content": row.content or "",
        "media_id": row.media_id,
        "media_type": row.media_type,
        "buttons": json.loads(row.buttons_json) if row.buttons_json else [],
    }


def get_custom_message_db(msg_type):
    """Get one custom message's data, or None if not configured."""
    db = get_db()
    try:
        row = db.query(CustomMessage).filter(CustomMessage.msg_type == msg_type).first()
        return _custom_message_row_to_dict(row) if row else None
    except Exception as e:
        print(f"Get custom message error: {e}")
        return None
    finally:
        db.close()


def set_custom_message_db(msg_type, data):
    """Set/replace one custom message's data."""
    db = get_db()
    try:
        row = db.query(CustomMessage).filter(CustomMessage.msg_type == msg_type).first()
        content_type = data.get("type", "text")
        content = data.get("content", "")
        media_id = data.get("media_id")
        media_type = data.get("media_type")
        buttons_json = json.dumps(data.get("buttons", []))
        if row:
            row.content_type = content_type
            row.content = content
            row.media_id = media_id
            row.media_type = media_type
            row.buttons_json = buttons_json
        else:
            db.add(CustomMessage(
                msg_type=msg_type,
                content_type=content_type,
                content=content,
                media_id=media_id,
                media_type=media_type,
                buttons_json=buttons_json,
            ))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Set custom message error: {e}")
        return False
    finally:
        db.close()


def get_all_custom_messages():
    """Get all custom messages as {msg_type: message_data_dict}."""
    db = get_db()
    try:
        rows = db.query(CustomMessage).all()
        return {r.msg_type: _custom_message_row_to_dict(r) for r in rows}
    except Exception as e:
        print(f"Get all custom messages error: {e}")
        return {}
    finally:
        db.close()


# =============================================================================
# CONTENT PROTECTION
# =============================================================================

def is_file_protected(message_id):
    """Whether a file (by db-channel message id) is flagged as protected."""
    db = get_db()
    try:
        return db.query(ProtectedFile).filter(ProtectedFile.message_id == message_id).first() is not None
    except Exception as e:
        print(f"Is file protected error: {e}")
        return False
    finally:
        db.close()


def add_protected_file_db(message_id):
    db = get_db()
    try:
        exists = db.query(ProtectedFile).filter(ProtectedFile.message_id == message_id).first()
        if not exists:
            db.add(ProtectedFile(message_id=message_id))
            db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Add protected file error: {e}")
        return False
    finally:
        db.close()


def remove_protected_file_db(message_id):
    db = get_db()
    try:
        row = db.query(ProtectedFile).filter(ProtectedFile.message_id == message_id).first()
        if row:
            db.delete(row)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Remove protected file error: {e}")
        return False
    finally:
        db.close()


def get_all_protected_message_ids():
    db = get_db()
    try:
        return [r.message_id for r in db.query(ProtectedFile).all()]
    except Exception as e:
        print(f"Get all protected message ids error: {e}")
        return []
    finally:
        db.close()


def sync_protected_files(message_ids):
    """Replace the protected-files set with the given iterable of ids."""
    db = get_db()
    try:
        target_ids = {int(mid) for mid in message_ids}
        existing = {r.message_id: r for r in db.query(ProtectedFile).all()}
        for mid, row in list(existing.items()):
            if mid not in target_ids:
                db.delete(row)
        for mid in target_ids:
            if mid not in existing:
                db.add(ProtectedFile(message_id=mid))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Sync protected files error: {e}")
        return False
    finally:
        db.close()


def set_content_limit_db(message_id, limit):
    """Set the remaining download count for a file, independent of protected status."""
    db = get_db()
    try:
        row = db.query(ContentDownloadLimit).filter(ContentDownloadLimit.message_id == message_id).first()
        if row:
            row.download_limit = limit
        else:
            db.add(ContentDownloadLimit(message_id=message_id, download_limit=limit))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Set content limit error: {e}")
        return False
    finally:
        db.close()


def try_consume_content_limit(message_id):
    """
    Atomically check-and-decrement a file's remaining download count.
    Returns (allowed, remaining): remaining is None when no limit is configured
    for this file (so the caller should treat it as unlimited).
    """
    db = get_db()
    try:
        row = db.query(ContentDownloadLimit).filter(ContentDownloadLimit.message_id == message_id).first()
        if not row:
            return True, None
        if row.download_limit <= 0:
            return False, 0
        row.download_limit -= 1
        remaining = row.download_limit
        db.commit()
        return True, remaining
    except Exception as e:
        db.rollback()
        print(f"Try consume content limit error: {e}")
        return True, None
    finally:
        db.close()


def get_all_content_limits():
    """Get all configured per-file limits as {message_id: remaining_limit}."""
    db = get_db()
    try:
        rows = db.query(ContentDownloadLimit).all()
        return {r.message_id: r.download_limit for r in rows}
    except Exception as e:
        print(f"Get all content limits error: {e}")
        return {}
    finally:
        db.close()


def sync_content_limits(limits_by_id):
    """Replace all per-file limits with the given {message_id: limit} dict."""
    db = get_db()
    try:
        target = {int(mid): limit for mid, limit in limits_by_id.items()}
        existing = {r.message_id: r for r in db.query(ContentDownloadLimit).all()}
        for mid, row in list(existing.items()):
            if mid not in target:
                db.delete(row)
        for mid, limit in target.items():
            if mid in existing:
                existing[mid].download_limit = limit
            else:
                db.add(ContentDownloadLimit(message_id=mid, download_limit=limit))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Sync content limits error: {e}")
        return False
    finally:
        db.close()


def cleanup_blocked_users(max_age_days=30):
    """
    Clean up old blocked/deleted users.
    Optionally hard delete users who have been blocked/deleted for more than max_age_days.
    """
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
