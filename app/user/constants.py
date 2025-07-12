"""Constants for user management and quota control."""

DAILY_QUOTA_LIMIT = 5
"""
Daily query quota limit

Maximum number of weather queries allowed for free users per day
"""

QUOTA_RESET_HOUR = 0
"""
Hour of day when the quota resets (UTC)

The daily quota resets at this time
"""
