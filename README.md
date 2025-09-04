# MMT-HTTP-Payment PayPal Payment API (FastAPI)

Dự án này cung cấp một API đơn giản để tích hợp thanh toán PayPal, bao gồm các chức năng **tạo đơn hàng**, **capture đơn hàng**, và **xem thông tin đơn hàng**.

## Creat Acount PayPal

- Truy cập: https://www.paypal.com/signup → đăng nhập bằng tài khoản PayPal thật.
- Chọn loại tài khoản: **Personal** dùng mua/bán cá nhân.
- Điền thông tin: email, mật khẩu, tên, số điện thoại…
- Xác minh email và số điện thoại theo hướng dẫn.
- Truy cập: https://developer.paypal.com/ đăng nhập bằng tài khoản PayPal thật.

![](https://images.ctfassets.net/drk57q8lctrm/21FLkQ2lbOCWynXsDZvXO5/485a163f199ef7749b914e54d4dc3335/paypal-logo.webp)

## ENV API Credentials
- Truy cập: https://developer.paypal.com/dashboard/applications/sandbox/ đăng nhập bằng tài khoản PayPal thật.

```sh
.env
PAYPAL_CLIENT_ID=Client ID
PAYPAL_SECRET=Secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```
- Test api https://developer.paypal.com/api/rest/authentication/
```sh
export $(grep -v '^#' .env | xargs)


curl -X POST "https://api-m.sandbox.paypal.com/v1/oauth2/token" \
  -u "$PAYPAL_CLIENT_ID:$PAYPAL_SECRET" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials"

```

- Result
```json
{
    "scope": "https://uri.paypal.com/services/invoicing https://uri.paypal.com/services/disputes/read-buyer https://uri.paypal.com/services/payments/realtimepayment https://uri.paypal.com/services/disputes/update-seller https://uri.paypal.com/services/payments/payment/authcapture openid https://uri.paypal.com/services/disputes/read-seller https://uri.paypal.com/services/payments/refund https://api-m.paypal.com/v1/vault/credit-card https://api-m.paypal.com/v1/payments/.* https://uri.paypal.com/payments/payouts https://api-m.paypal.com/v1/vault/credit-card/.* https://uri.paypal.com/services/subscriptions https://uri.paypal.com/services/applications/webhooks",
    "access_token": "A21AAFEpH4PsADK7qSS7pSRsgzfENtu-Q1ysgEDVDESseMHBYXVJYE8ovjj68elIDy8nF26AwPhfXTIeWAZHSLIsQkSYz9ifg",
    "token_type": "Bearer",
    "app_id": "APP-80W284485P519543T",
    "expires_in": 31668,
    "nonce": "2020-04-03T15:35:36ZaYZlGvEkV4yVSz8g6bAKFoGSEzuy3CQcz3ljhibkOHg"
}
```



## API Endpoints

### 1. `POST /create-order` https://developer.paypal.com/docs/api/orders/v2/#orders_create
- **Mục đích:** Tạo một đơn hàng mới trên PayPal.
- **Tham số:**
  - `amount` (float, query param): số tiền cần thanh toán (USD).
- **Trả về:**
  - JSON chứa `order_id`, `status`, và `links` (approve URL, capture URL...).

---

### 2. `POST /capture-order/{order_id}` https://developer.paypal.com/docs/api/orders/v2/#orders_capture
- **Mục đích:** Capture (xác nhận thanh toán) một đơn hàng đã được approve trên PayPal.
- **Tham số:**
  - `order_id` (path param): ID của đơn hàng PayPal.
- **Trả về:**
  - JSON chi tiết giao dịch sau khi thanh toán thành công.

---

### 3. `GET /order-info/{order_id}` https://developer.paypal.com/docs/api/orders/v2/#orders_get
- **Mục đích:** Lấy thông tin chi tiết của một đơn hàng PayPal (dù đã capture hay chưa).
- **Tham số:**
  - `order_id` (path param): ID của đơn hàng.
- **Trả về:**
  - JSON với trạng thái (`CREATED`, `APPROVED`, `COMPLETED`), số tiền, người thanh toán...

---

### 4. `GET /success` *(ẩn khỏi Swagger UI)*
- **Mục đích:** Trang callback khi thanh toán thành công.  
- **Tham số:**
  - `token` (query param): Order ID PayPal trả về sau khi người dùng approve.  
- **Trả về:**  
  - HTML hiển thị thông báo "Payment Successful" và mã đơn hàng.

---

### 5. `GET /cancel` *(ẩn khỏi Swagger UI)*
- **Mục đích:** Trang callback khi người dùng hủy thanh toán.  
- **Tham số:**
  - `token` (query param): Order ID (nếu có).  
- **Trả về:**  
  - HTML hiển thị thông báo "Payment Cancelled" và mã đơn hàng.

---

### Luồng hoạt động

1. Gọi `POST /create-order?amount=100.00` để tạo đơn hàng.  
   - API trả về `order_id` và link `approve`.  
2. Frontend redirect người dùng sang link `approve`.  
3. Sau khi approve, PayPal gọi redirect về `/success?token={order_id}` hoặc `/cancel?token={order_id}`.  
4. Nếu thành công, có thể gọi `POST /capture-order/{order_id}` để xác nhận thanh toán.  
5. Có thể kiểm tra chi tiết đơn hàng bằng `GET /order-info/{order_id}`

![](./images/paypal.gif)

---

## Mailpit

[Mailpit](https://github.com/axllent/mailpit) là một công cụ giả lập SMTP server và web UI để kiểm tra email trong môi trường phát triển.  
Nó cho phép developer gửi email từ ứng dụng và xem trực tiếp trong giao diện web thay vì gửi thật ra ngoài.

### Cách chạy Mailpit bằng Docker

```sh
docker run -d \
  --name mailpit \
  -p 1025:1025 \
  -p 8025:8025 \
  axllent/mailpit
```

- SMTP Server: localhost:1025
- Web UI: http://localhost:8025

### Mô tả giao thức SMTP

- SMTP hoạt động dựa trên mô hình client–server:

- Client (Mail User Agent - MUA): chương trình người dùng (ví dụ Outlook, Thunderbird).

- Server (Mail Transfer Agent - MTA): dịch vụ mail (Postfix, Sendmail, Gmail SMTP server).

```sh
Client:   HELO client.example.com
Server:   250 Hello client.example.com
Client:   MAIL FROM:<alice@example.com>
Server:   250 OK
Client:   RCPT TO:<bob@example.com>
Server:   250 OK
Client:   DATA
Server:   354 End data with <CR><LF>.<CR><LF>
Client:   Subject: Test Mail
          Hello Bob, this is a test.
          .
Server:   250 OK id=12345
Client:   QUIT
Server:   221 Bye
```

![](./images/mail.gif)


## File docker-compose.yml dùng để chạy toàn bộ hệ thống (FastAPI + Mailpit) chỉ với một lệnh duy nhất.

```sh
version: "3.9"

services:
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi_app
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - mailpit

  mailpit:
    image: axllent/mailpit:latest
    container_name: mailpit
    restart: always
    ports:
      - "8025:8025" # giao diện web Mailpit
      - "1025:1025" # SMTP server
```

### fastapi

- **build:** build image từ thư mục hiện tại (.) dựa trên Dockerfile.
- **container_name:** tên container là fastapi_app.
- **ports:** ánh xạ 8000 trong container ra localhost:8000.
- **volumes:** mount code từ máy host vào container để hot-reload khi code thay đổi.
- **depends_on:** đảm bảo mailpit chạy trước khi fastapi start.

### mailpit

- **image:** dùng image axllent/mailpit:latest.
- **ports:**
  - **8025:8025** → giao diện web Mailpit (xem email).
  - **1025:1025** → SMTP server để FastAPI gửi mail.

### Cách chạy `docker-compose up --build`
- **FastAPI docs:** http://localhost:8000/docs
- **Mailpit UI:** http://localhost:8025