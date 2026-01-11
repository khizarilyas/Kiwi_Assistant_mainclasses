from dataclasses import dataclass  # Lets us create classes meant to store data
from datetime import datetime, timezone, timedelta  # datetime = timestamps, timezone = timezone-aware UTC

# A dataclass to conveniently define a class that mainly stores data.
@dataclass(frozen=True)
class Session:
    started_at: datetime  # When the session record was created
    active: bool          # Whether the session is currently active


class SessionService:
    # Type hint: this class has an attribute called session which should be a Session object
    session: Session

    def __init__(self):
        # Initialize the service with a session that is not active
        self.session = Session(started_at=datetime.now(timezone.utc), active=False)

    def start_session(self):
        """
        Starts a new session by creating a new Session object.
        """
        self.session = Session(started_at=datetime.now(timezone.utc), active=True)
        return self.session

    def session_active(self, timeout_seconds: int = 5) -> bool:
        """
        True if session is marked active AND within timeout window.
        """
        if not self.session.active:
            return False

        expires_at = self.session.started_at + timedelta(seconds=timeout_seconds)
        return datetime.now(timezone.utc) <= expires_at

    def terminate_session(self):
        """
        Terminates (ends) the session by creating a new Session object.
        """
        self.session = Session(started_at=datetime.now(timezone.utc), active=False)
        return self.session












