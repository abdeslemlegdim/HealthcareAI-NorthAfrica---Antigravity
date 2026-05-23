"""
Rate Limiter for authentication endpoints.

This module provides rate limiting functionality to protect against brute force
attacks and abuse. Supports both Redis (preferred) and in-memory storage (fallback).

Requirements: 10.2, 10.3, 10.4, 10.5
"""

import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class RateLimiter:
    """
    Rate limiter for authentication endpoints.
    
    Implements sliding window rate limiting with support for Redis (distributed)
    and in-memory storage (single instance fallback).
    
    Configured limits:
    - Login: 5 attempts per email per 15 minutes
    - Registration: 10 attempts per IP per hour
    - Token refresh: 20 attempts per user per hour
    """
    
    def __init__(self, redis_client: Optional[any] = None):
        """
        Initialize RateLimiter.
        
        Args:
            redis_client: Optional Redis client for distributed rate limiting.
                         If None, uses in-memory storage.
        """
        self.redis = redis_client
        self.memory_store: Dict[str, List[float]] = defaultdict(list)
        
        # Rate limit configurations
        self.limits = {
            "login": {"max_attempts": 5, "window_seconds": 900},  # 15 minutes
            "register": {"max_attempts": 10, "window_seconds": 3600},  # 1 hour
            "refresh": {"max_attempts": 20, "window_seconds": 3600}  # 1 hour
        }
    
    async def check_rate_limit(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if rate limit exceeded.
        
        Uses sliding window algorithm to track attempts within the time window.
        
        Args:
            key: Unique identifier for rate limiting (e.g., "login:user@example.com")
            max_attempts: Maximum number of attempts allowed
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
            - allowed: True if request is allowed, False if rate limited
            - retry_after_seconds: Seconds until rate limit resets (None if allowed)
        
        Requirements: 10.2, 10.3, 10.4, 10.5
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if self.redis:
            return await self._check_redis_rate_limit(
                key, max_attempts, window_seconds, current_time, window_start
            )
        else:
            return await self._check_memory_rate_limit(
                key, max_attempts, window_seconds, current_time, window_start
            )
    
    async def _check_redis_rate_limit(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
        current_time: float,
        window_start: float
    ) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit using Redis storage.
        
        Uses Redis sorted sets for efficient sliding window implementation.
        
        Args:
            key: Rate limit key
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
            current_time: Current timestamp
            window_start: Window start timestamp
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        redis_key = f"rate_limit:{key}"
        
        try:
            # Remove old entries outside the window
            self.redis.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current attempts in window
            current_attempts = self.redis.zcard(redis_key)
            
            if current_attempts >= max_attempts:
                # Get oldest entry to calculate retry_after
                oldest_entries = self.redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_timestamp = oldest_entries[0][1]
                    retry_after = int(oldest_timestamp + window_seconds - current_time)
                    return False, max(1, retry_after)
                return False, window_seconds
            
            # Add current attempt
            self.redis.zadd(redis_key, {str(current_time): current_time})
            
            # Set expiration on the key
            self.redis.expire(redis_key, window_seconds)
            
            return True, None
            
        except Exception as e:
            # Fallback to memory storage if Redis fails
            print(f"Redis rate limit check failed: {e}. Falling back to memory storage.")
            return await self._check_memory_rate_limit(
                key, max_attempts, window_seconds, current_time, window_start
            )
    
    async def _check_memory_rate_limit(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
        current_time: float,
        window_start: float
    ) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit using in-memory storage.
        
        Uses Python dictionary with timestamp lists for sliding window.
        
        Args:
            key: Rate limit key
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
            current_time: Current timestamp
            window_start: Window start timestamp
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        # Remove old entries outside the window
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key]
            if timestamp > window_start
        ]
        
        current_attempts = len(self.memory_store[key])
        
        if current_attempts >= max_attempts:
            # Calculate retry_after based on oldest entry
            if self.memory_store[key]:
                oldest_timestamp = min(self.memory_store[key])
                retry_after = int(oldest_timestamp + window_seconds - current_time)
                return False, max(1, retry_after)
            return False, window_seconds
        
        # Add current attempt
        self.memory_store[key].append(current_time)
        
        return True, None
    
    async def reset_rate_limit(self, key: str) -> None:
        """
        Reset rate limit for key.
        
        Clears all attempts for the specified key. Useful for testing or
        manual intervention.
        
        Args:
            key: Rate limit key to reset
        """
        if self.redis:
            try:
                redis_key = f"rate_limit:{key}"
                self.redis.delete(redis_key)
            except Exception as e:
                print(f"Redis rate limit reset failed: {e}")
        
        # Also clear from memory store
        if key in self.memory_store:
            del self.memory_store[key]
    
    async def check_login_rate_limit(self, email: str) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit for login attempts.
        
        Limit: 5 attempts per email per 15 minutes
        
        Args:
            email: Email address attempting login
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        
        Requirements: 10.2, 10.3
        """
        key = f"login:{email}"
        config = self.limits["login"]
        return await self.check_rate_limit(
            key,
            config["max_attempts"],
            config["window_seconds"]
        )
    
    async def check_register_rate_limit(self, ip_address: str) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit for registration attempts.
        
        Limit: 10 attempts per IP per hour
        
        Args:
            ip_address: IP address attempting registration
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        
        Requirements: 10.4
        """
        key = f"register:{ip_address}"
        config = self.limits["register"]
        return await self.check_rate_limit(
            key,
            config["max_attempts"],
            config["window_seconds"]
        )
    
    async def check_refresh_rate_limit(self, user_id: int) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit for token refresh attempts.
        
        Limit: 20 attempts per user per hour
        
        Args:
            user_id: User ID attempting token refresh
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        
        Requirements: 10.5
        """
        key = f"refresh:{user_id}"
        config = self.limits["refresh"]
        return await self.check_rate_limit(
            key,
            config["max_attempts"],
            config["window_seconds"]
        )
    
    def get_remaining_attempts(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> int:
        """
        Get remaining attempts for a key.
        
        Args:
            key: Rate limit key
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
        
        Returns:
            Number of remaining attempts
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if self.redis:
            try:
                redis_key = f"rate_limit:{key}"
                self.redis.zremrangebyscore(redis_key, 0, window_start)
                current_attempts = self.redis.zcard(redis_key)
                return max(0, max_attempts - current_attempts)
            except Exception:
                pass
        
        # Fallback to memory store
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key]
            if timestamp > window_start
        ]
        current_attempts = len(self.memory_store[key])
        return max(0, max_attempts - current_attempts)
