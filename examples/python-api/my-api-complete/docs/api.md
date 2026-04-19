# RestaurantOrderAPI - Dokumentacja API

REST API do zarządzania zamówieniami restauracji. Pozwala na tworzenie, przeglądanie, aktualizowanie i usuwanie zamówień klientów, a także zarządzanie ich statusami.

---

## Spis treści

- [1. Wprowadzenie](#1-wprowadzenie)
- [2. Bazy danych - Model danych](#2-bazy-danych---model-danych)
- [3. Uwierzytelnianie](#3-uwierzytelnianie)
- [4. Endpoints](#4-endpoints)
  - [GET /orders](#get-orders)
  - [GET /orders/{id}](#get-ordersid)
  - [POST /orders](#post-orders)
  - [PUT /orders/{id}](#put-ordersid)
  - [DELETE /orders/{id}](#delete-ordersid)
- [5. Przykłady żądań i odpowiedzi](#5-przykłady-żądań-i-odpowiedzi)
- [6. Wdrażanie aplikacji](#6-wdrażanie-aplikacji)
- [7. Licencja](#7-licencja)

---

## 1. Wprowadzenie

`RestaurantOrderAPI` to RESTowe API umożliwiające zarządzanie zamówieniami w systemie restauracji. Aplikacja umożliwia:

- Tworzenie nowych zamówień
- Pobieranie listy zamówień
- Pobieranie szczegółów konkretnego zamówienia
- Aktualizowanie statusu zamówienia
- Usuwanie zamówień

API jest zbudowane zgodnie z zasadami REST, wykorzystuje format JSON do wymiany danych i obsługuje standardowe kody odpowiedzi HTTP.

---

### Tabela: `orders`

| Pole            | Typ danych       | Opis                                      |
|-----------------|------------------|-------------------------------------------|
| `id`            | UUID / Integer   | Unikalny identyfikator zamówienia         |
| `customer_name` | String (100)     | Imię i nazwisko klienta                   |
| `table_number`  | Integer          | Numer stolika (opcjonalnie)               |
| `items`         | JSON             | Lista pozycji w zamówieniu                |
| `total_price`   | Decimal (10,2)   | Łączna cena zamówienia                    |
| `status`        | String (20)      | Status zamówienia (np. "pending", "ready", "delivered") |
| `created_at`    | DateTime         | Data i czas utworzenia zamówienia         |
| `updated_at`    | DateTime         | Data i czas ostatniej aktualizacji        |

Przykład danych w polu `items`:
[
  { "name": "Pizza Margherita", "quantity": 2, "price": 35.00 },
  { "name": "Cola", "quantity": 1, "price": 8.00 }
]

---

## 3. Uwierzytelnianie

API wymaga uwierzytelnienia przy użyciu nagłówka `Authorization` z tokenem Bearer.

### Sposób działania:
- Użytkownik otrzymuje token (np. po zalogowaniu się przez panel administracyjny).
- Token musi być dołączony do każdego żądania.

### Przykład nagłówka:
Authorization: Bearer <your-jwt-token>

Jeśli token jest nieprawidłowy lub brakuje go, API zwraca:
{
  "error": "Unauthorized",
  "message": "Brak dostępu. Token wymagany."
}
**Status HTTP: 401 Unauthorized**

---

### `GET /orders`

Pobiera listę wszystkich zamówień.

#### Parametry zapytania (opcjonalne):
- `status` – filtruj zamówienia po statusie (np. `pending`, `ready`)
- `limit` – maksymalna liczba zamówień do zwrócenia (domyślnie 20)
- `page` – numer strony (domyślnie 1)

#### Odpowiedź:
- **200 OK** – lista zamówień

#### Przykład:
GET /orders?status=pending&limit=10&page=1

---

### `GET /orders/{id}`

Pobiera szczegóły konkretnego zamówienia.

#### Parametry:
- `id` – UUID lub liczba całkowita identyfikująca zamówienie

#### Odpowiedź:
- **200 OK** – szczegóły zamówienia
- **404 Not Found** – jeśli zamówienie nie istnieje

#### Przykład:
GET /orders/123e4567-e89b-12d3-a456-426614174000

---

### `POST /orders`

Tworzy nowe zamówienie.

#### Nagłówki wymagane:
- `Content-Type: application/json`
- `Authorization: Bearer <token>`

#### Ciało żądania (przykład):
{
  "customer_name": "Jan Kowalski",
  "table_number": 12,
  "items": [
    {
      "name": "Spaghetti Bolognese",
      "quantity": 1,
      "price": 29.99
    },
    {
      "name": "Water",
      "quantity": 2,
      "price": 4.00
    }
  ],
  "total_price": 37.99,
  "status": "pending"
}

#### Odpowiedź:
- **201 Created** – zamówienie utworzone
- **400 Bad Request** – błędy walidacji (np. brak wymaganych pól)

---

### `PUT /orders/{id}`

Aktualizuje istniejące zamówienie (np. zmienia status).

#### Ciało żądania (przykład):
{
  "status": "ready"
}

> Uwaga: Można aktualizować tylko pola `status`, `table_number` i `items`. Pola `customer_name` i `total_price` są tylko do odczytu po utworzeniu.

#### Odpowiedź:
- **200 OK** – zamówienie zaktualizowane
- **404 Not Found** – zamówienie nie istnieje
- **400 Bad Request** – nieprawidłowe dane

---

#### Odpowiedź:
- **204 No Content** – zamówienie usunięte
- **404 Not Found** – zamówienie nie istnieje

> Uwaga: Usunięcie zamówienia jest trwałe.

---

### Przykład 1: Pobranie listy zamówień

**Żądanie:**
GET /orders?status=pending HTTP/1.1
Host: api.restaurant.local
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx

**Odpowiedź:**
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "customer_name": "Anna Nowak",
    "table_number": 5,
    "items": [
      {
        "name": "Pizza Pepperoni",
        "quantity": 1,
        "price": 40.00
      }
    ],
    "total_price": 40.00,
    "status": "pending",
    "created_at": "2025-04-05T10:00:00Z",
    "updated_at": "2025-04-05T10:00:00Z"
  }
]

---

### Przykład 2: Utworzenie zamówienia

**Żądanie:**
POST /orders HTTP/1.1
Host: api.restaurant.local
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx

{
  "customer_name": "Piotr Wiśniewski",
  "table_number": 8,
  "items": [
    {
      "name": "Caesar Salad",
      "quantity": 1,
      "price": 25.00
    }
  ],
  "total_price": 25.00,
  "status": "pending"
}

**Odpowiedź:**
HTTP/1.1 201 Created
Location: /orders/1a2b3c4d-e5f6-7890-1234-56789abcdef0

{
  "id": "1a2b3c4d-e5f6-7890-1234-56789abcdef0",
  "customer_name": "Piotr Wiśniewski",
  "table_number": 8,
  "items": [
    {
      "name": "Caesar Salad",
      "quantity": 1,
      "price": 25.00
    }
  ],
  "total_price": 25.00,
  "status": "pending",
  "created_at": "2025-04-05T11:30:00Z",
  "updated_at": "2025-04-05T11:30:00Z"
}

---

### Przykład 3: Aktualizacja statusu zamówienia

**Żądanie:**
PUT /orders/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx

{
  "status": "delivered"
}

**Odpowiedź:**
HTTP/1.1 200 OK

{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_name": "Anna Nowak",
  "table_number": 5,
  "items": [
    {
      "name": "Pizza Pepperoni",
      "quantity": 1,
      "price": 40.00
    }
  ],
  "total_price": 40.00,
  "status": "delivered",
  "created_at": "2025-04-05T10:00:00Z",
  "updated_at": "2025-04-05T12:15:00Z"
}

---

### Wymagania:
- Python 3.9+
- PostgreSQL 12+ (lub SQLite dla testów)
- pip
- virtualenv (opcjonalnie)

### Kroki:

1. **Sklonuj repozytorium:**
      git clone https://github.com/example/restaurant-order-api.git
   cd restaurant-order-api
   
2. **Utwórz środowisko wirtualne:**
      python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # lub
   venv\Scripts\activate     # Windows
   
3. **Zainstaluj zależności:**
      pip install -r requirements.txt
   
4. **Skonfiguruj zmienne środowiskowe:**
   Utwórz plik `.env`:
      DATABASE_URL=postgresql://user:password@localhost/restaurant_db
   SECRET_KEY=twoj_bardzo_tajny_klucz_jwt
   DEBUG=False
   
5. **Uruchom migracje (przykład z Django):**
      python manage.py migrate
   
6. **Uruchom serwer:**
      python manage.py runserver 0.0.0.0:8000
   
7. **Dostęp do API:**
      http://localhost:8000/orders
   
### Wdrożenie produkcyjne (np. z użyciem Docker i Nginx):

1. Zbuduj obraz Docker:
      docker build -t restaurant-order-api .
   
2. Uruchom kontener:
      docker run -d -p 8000:8000 --env-file .env --name restaurant-api restaurant-order-api
   
3. Skonfiguruj Nginx jako reverse proxy i dodaj SSL (np. z Let's Encrypt).

---

## 7. Licencja

Ta dokumentacja i kod API są udostępniane na licencji MIT.

© 2025 RestaurantOrderAPI. Wszelkie prawa zastrzeżone.