from app.core.loop import ensure_selector_loop

ensure_selector_loop()  # must run at import time, before uvicorn creates its loop

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)