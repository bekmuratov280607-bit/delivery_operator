# Glovo Delivery FastAPI — баштоо

## 1. Виртуалдык чөйрө (Windows PowerShell)
```powershell
py -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Gemini API ачкычы
`.env.example` файлын көчүрүп, көчүрмөнү `.env` деп атаңыз. Google AI Studio'дон Gemini API ачкычын алып, `.env` файлына коюңуз:
```env
GEMINI_API_KEY=чыныгы_ачкыч
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///./glovo.db
```
Ачкычты кодго түз жазбаңыз жана эч кимге жибербеңиз.

## 3. Серверди иштетүү
```powershell
uvicorn main:app --reload
```
Swagger: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

## 4. Postman тесттери

### A. Товар кошуу
POST `http://127.0.0.1:8000/products/` — Body → raw → JSON:
```json
{
  "product_name": "Телефон",
  "price": 77000,
  "description": "iPhone 16 Pro Max 256GB gold",
  "stock": 5
}
```
Күтүлгөн жооп: `201 Created`. Жооптогу `id` маанисин эстеп калыңыз.

### B. Товарларды көрүү
GET `http://127.0.0.1:8000/products/`

### C. Товар издөө
GET `http://127.0.0.1:8000/products/search?q=Телефон`

### D. Заказ түзүү
POST `http://127.0.0.1:8000/orders/` — Body → raw → JSON:
```json
{
  "customer_name": "Бек",
  "phone": "+996700000000",
  "address": "Бишкек, Чүй көчөсү 1",
  "product_id": 1,
  "quantity": 1
}
```
`product_id` ордуна A кадамында кайтарылган чыныгы ID'ни коюңуз. Күтүлгөн жооп: `201 Created`.

### E. Заказды көрүү
GET `http://127.0.0.1:8000/orders/1` — өз заказ ID'ңизди колдонуңуз.

### F. AI суроосу
POST `http://127.0.0.1:8000/ai/answer/` — Body → raw → JSON:
```json
{
  "message": "Телефон барбы жана баасы канча?"
}
```

### G. Заказ тууралуу AI
POST `http://127.0.0.1:8000/ai/answer/`:
```json
{
  "message": "Заказым кайсы абалда?",
  "order_id": 1
}
```

### H. Көйгөйдү талдоо
POST `http://127.0.0.1:8000/ai/analysis/`:
```json
{
  "message": "Заказым кечигип жатат, эмне кылсам болот?",
  "order_id": 1
}
```

### I. Статусту өзгөртүү
PATCH `http://127.0.0.1:8000/orders/1/status`:
```json
{"order_status": "confirmed"}
```
Мүмкүн болгон статустар: `pending`, `confirmed`, `cancelled`, `delivered`.

## Эскертүүлөр
- SQLite `glovo.db` базасы автоматтык түзүлөт.
- Заказ түзүлгөндө кампадагы `stock` азаят.
- Gemini ачкычы жок болсо, AI endpoint `503` кайтарат; товар жана заказ endpoint'тери иштей берет.
- Бул баштапкы окуу версиясы: авторизация, төлөм, курьердин GPS көзөмөлү азырынча жок.
