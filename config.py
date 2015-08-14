#coding=utf-8

'''
    configuration of hawkeye client.

    @author: leotse
'''
# host name
SERVER_NAME = "Server43"


# hawkeye host settings
HAWKEYE_HOST = "HAWKEYE_HOST"
HAWKEYE_PORT = 8000

# threshold settings
CPU_USAGE_THRESHOLD = 0.6
DISK_USAGE_THRESHOLD = 0.7

# api settigns
API_NAME = "health_report"
TIMEOUT = 5

# health status
class HealthStatus:
    HEALTH = 'HEALTH'
    SICK = 'SICK'
