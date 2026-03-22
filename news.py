import requests
import datetime
import logging

logger = logging.getLogger(__name__)

class NewsFilter:
    def __init__(self, pause_mins_before=15, pause_mins_after=15):
        self.pause_mins_before = pause_mins_before
        self.pause_mins_after = pause_mins_after
        # Free JSON endpoint widely used for basic forex factory data
        self.api_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        self.high_impact_events = []
        
    def update_calendar(self):
        """Fetches the latest economic calendar events."""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Filter for USD high impact events
                self.high_impact_events = [
                    event for event in data 
                    if event.get('country') == 'USD' and event.get('impact') == 'High'
                ]
                logger.info(f"Fetched {len(self.high_impact_events)} high impact USD events for the week.")
            else:
                logger.warning(f"Failed to fetch news calendar, HTTP Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch news calendar due to an exception: {e}")
            
    def is_trading_allowed(self):
        """Checks if current time is outside the pause window of any high-impact event."""
        if not self.high_impact_events:
            return True # If fail to fetch, safely default to trading allowed.
            
        # Using localized time in UTC depending on environment. For safety, assume UTC
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for event in self.high_impact_events:
            event_time_str = event.get('date')
            try:
                # ISO Time parse: 2023-11-01T08:30:00-04:00
                # Python 3.7+ supports fromisoformat natively
                try:
                    event_time = datetime.datetime.fromisoformat(event_time_str)
                    if event_time.tzinfo is None:
                        event_time = event_time.replace(tzinfo=datetime.timezone.utc)
                except ValueError:
                    # Fallback string manipulation if iso format fails
                    continue
            except Exception:
                continue
                
            # Compute time difference in minutes
            delta_mins = (now - event_time).total_seconds() / 60.0
            
            # If we are within the window before or after
            if -self.pause_mins_before <= delta_mins <= self.pause_mins_after:
                logger.warning(f"Trading paused due to High Impact News: {event.get('title')} at {event_time_str}")
                return False
                
        return True
