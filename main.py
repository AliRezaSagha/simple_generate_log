from fastapi import FastAPI, Request
import logging
import uuid

app = FastAPI()

# تنظیم لاگر برای خروجی JSON روی کنسول
logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"asctime": "%(asctime)s", "levelname": "%(levelname)s", "message": "%(message)s", "request_id": "%(request_id)s", "email": "%(email)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

@app.post("/register")
async def register(request: Request):
    body = await request.json()
    request_id = str(uuid.uuid4())
    email = body.get("email")

    logger.info("register_attempt", extra={"request_id": request_id, "email": email})

    # شبیه‌سازی یک تأخیر کوتاه برای طبیعی‌تر شدن لاگ
    return {"message": f"user {email} registered successfully", "request_id": request_id}


@app.on_event("startup")
async def startup_event():
    logger.info("app_startup", extra={"request_id": None, "email": None})
