from zoneinfo import available_timezones


PRIORITY_TIME_ZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Phoenix",
    "America/Los_Angeles",
    "America/Anchorage",
    "Pacific/Honolulu",
    "UTC",
]


def time_zone_choices():
    zones = sorted(available_timezones())
    priority = [zone for zone in PRIORITY_TIME_ZONES if zone in zones]
    remaining = [zone for zone in zones if zone not in priority]
    return [(zone, zone) for zone in [*priority, *remaining]]
