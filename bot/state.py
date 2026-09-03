"""
User state management with Redis backend and in-memory fallback.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory state storage")

# Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
SESSION_TTL_SECONDS = int(os.getenv('SESSION_TTL_SECONDS', '1800'))

# In-memory fallback
_memory_store = {}

# Redis client (lazy initialization)
_redis_client = None

# Restart-flow guidance shown whenever we can't trust the state
RESTART_MESSAGE = (
    "⚠️ اطلاعات جلسه شما یافت نشد یا منقضی شده است.\n"
    "لطفاً دوباره با /start شروع کنید."
)


def _get_redis():
    """Get or create Redis client."""
    global _redis_client
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}, falling back to memory")
            _redis_client = False  # Sentinel to avoid retrying
            return None
    
    return _redis_client if _redis_client is not False else None


def _redis_key(user_id):
    """Generate Redis key for user session."""
    return f"astro:session:{user_id}"


def get_state(user_id):
    """Get user state by ID."""
    redis_client = _get_redis()
    
    if redis_client:
        try:
            data = redis_client.get(_redis_key(user_id))
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
    
    # Fallback to memory
    return _memory_store.get(user_id)


def set_state(user_id, state):
    """Set user state with TTL."""
    redis_client = _get_redis()
    
    if redis_client:
        try:
            redis_client.setex(
                _redis_key(user_id),
                SESSION_TTL_SECONDS,
                json.dumps(state)
            )
            return
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
    
    # Fallback to memory
    _memory_store[user_id] = state


def delete_state(user_id):
    """Delete user state."""
    redis_client = _get_redis()
    
    if redis_client:
        try:
            redis_client.delete(_redis_key(user_id))
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
    
    # Also clean memory
    _memory_store.pop(user_id, None)


def init_state(user_id):
    """Initialize a new user state for chart creation."""
    state = {
        'step': 'name',
        'data': {}
    }
    set_state(user_id, state)
    return state
