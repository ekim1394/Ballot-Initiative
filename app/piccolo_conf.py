from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine

DB = SQLiteEngine()
APP_REGISTRY = AppRegistry(
    apps=["voter_records.piccolo_app", "piccolo_admin.piccolo_app"]
)
