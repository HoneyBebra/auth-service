from pydantic_settings import BaseSettings


class RateLimitSettings(BaseSettings):
    login_max_failed_attempts: int = 5

    # Failures are counted during this period
    login_failed_window_seconds: int = 900  # 15 min

    # Period of blocking after {login_max_failed_attempts} attempts
    login_lock_duration_seconds: int = 900  # 15 min

    # Redis key prefix
    rate_limit_redis_prefix: str = "auth:rl"
