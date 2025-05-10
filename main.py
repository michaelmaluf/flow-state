from database import Database

DB_URL = "postgresql://percules:***REMOVED***@localhost:5432/flow_state"

# Initialize the database
db = Database(DB_URL)
db.create_tables()


# Track application usage
def track_app_usage(app_name, seconds, is_productive=None):
    db.update_application_time(app_name, seconds, is_productive)


# Manage sessions
active_session_id = None
interruptions = 0


def start_session(app_name=None):
    global active_session_id
    # active_session_id = db.start_session(app_name)
    return active_session_id


def end_session():
    global active_session_id, interruptions
    if active_session_id:
        db.end_session(active_session_id, interruptions)
        active_session_id = None
        interruptions = 0


def handle_app_change(new_app_name, is_productive=None):
    global active_session_id, interruptions

    # Update time for the app
    track_app_usage(new_app_name, 10, is_productive)  #

    if is_productive:
        if not active_session_id:
            start_session(new_app_name)
    else:
        if active_session_id:
            interruptions += 1
            # End session if interruption is too long
            # (In real app, you'd track time in non-productive app)
            end_session()


def get_stats_for_pi():
    stats = db.get_today_stats()
    return {
        'productive_seconds': stats['productive_time'],
        'non_productive_seconds': stats['non_productive_time']
    }


if __name__ == "__main__":
    # Initialize DB
    db.create_tables()

    handle_app_change("VSCode", True)
    handle_app_change("YouTube", False)

    print(db.get_today_stats())
