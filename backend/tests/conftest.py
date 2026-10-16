import os

os.environ.setdefault("DATABASE_URL", "postgresql://postgres@localhost:5433/eid")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123456")
os.environ["COLLECTORS_ENABLED"] = "false"
