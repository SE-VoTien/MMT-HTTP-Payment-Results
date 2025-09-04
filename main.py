from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
import requests
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# ---------------- Config ----------------
load_dotenv()
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))  # default mailpit
SMTP_USER = os.getenv("SMTP_USER", "no-reply@example.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "admin@example.com")

# ---------------- Mail Helper ----------------
def send_order_email(subject: str, order_info: dict):
    """Send email with order details"""
    try:
        body = f"""
<div style="font-family: Arial, sans-serif; background:#f9f9f9; padding:20px;">
    <h2 style="color:#2c3e50; text-align:center;">{subject}</h2>
    <div style="background:#fff; padding:20px; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
        <p style="font-size:16px; color:#333;">
            <b style="color:#007BFF;">Order ID:</b> 
            <span style="font-size:18px; color:#000;">{order_info.get("id")}</span>
        </p>
        <p style="font-size:16px; color:#333;">
            <b style="color:#28a745;">Status:</b> 
            <span style="font-size:18px; font-weight:bold; color:#28a745;">{order_info.get("status")}</span>
        </p>
        <p style="font-size:16px; color:#333;">
            <b style="color:#e67e22;">Amount:</b> 
            <span style="font-size:18px; color:#000;">{order_info.get("purchase_units", [{}])[0].get("amount")}</span>
        </p>
    </div>
</div>
"""

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = RECEIVER_EMAIL

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_PORT == 587:
                server.starttls()
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"[MAIL] Sent: {subject} → {RECEIVER_EMAIL}")

    except Exception as e:
        print(f"[MAIL ERROR] {e}")

# ---------------- PayPal Helper ----------------
def get_access_token():
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    resp = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    if resp.status_code == 200:
        return resp.json()["access_token"]
    else:
        raise Exception(f"PayPal auth failed: {resp.status_code} {resp.text}")

def create_order(amount: float):
    token = get_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    json_data = {
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": f"{amount:.2f}"}}],
        "application_context": {
            "return_url": "http://localhost:8000/success",
            "cancel_url": "http://localhost:8000/cancel"
        }
    }
    resp = requests.post(url, headers=headers, json=json_data)
    if resp.status_code == 201:
        return resp.json()
    else:
        raise Exception(f"Create order failed: {resp.status_code} {resp.text}")

def capture_order(order_id: str):
    token = get_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    resp = requests.post(url, headers=headers)
    if resp.status_code == 201:
        return resp.json()
    else:
        raise Exception(f"Capture failed: {resp.status_code} {resp.text}")

def get_order_info(order_id: str):
    token = get_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        return {"error": resp.text, "status_code": resp.status_code}

# ---------------- FastAPI ----------------
app = FastAPI(
    title="PayPal Payment API",
    description="API for creating, capturing, and checking PayPal orders",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # Redoc
)

router = APIRouter(tags=["PayPal"])

@router.post("/create-order")
def api_create_order(amount: float):
    return create_order(amount)

@router.post("/capture-order/{order_id}")
def api_capture_order(order_id: str):
    order_info = capture_order(order_id)
    send_order_email("Order Captured", order_info)
    return order_info

@router.get("/order-info/{order_id}")
def api_order_info(order_id: str):
    return get_order_info(order_id)

@router.get("/success", include_in_schema=False)
def success(token: str):
    order_info = get_order_info(token)
    send_order_email("Payment Success", order_info)
    return HTMLResponse(content=f'<h2 style="color:green;">Payment Successful {order_info.get("id")}!</h2>')

@router.get("/cancel", include_in_schema=False)
def cancel(token: str):
    order_info = get_order_info(token)
    send_order_email("Payment Cancelled", order_info)
    return HTMLResponse(content=f'<h2 style="color:red;">Payment Cancelled {order_info.get("id")}!</h2>')

# ---------------- Include router ----------------
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",         # tên file (main.py) + object app
        host="0.0.0.0",     # cho phép truy cập từ mọi IP
        port=8000,          # cổng chạy server
        reload=True         # tự reload khi code thay đổi
    )
