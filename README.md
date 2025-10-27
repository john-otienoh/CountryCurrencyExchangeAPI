# 🌍 Country Currency & Exchange API — FastAPI Project

## 📘 Overview

A RESTful API built with **FastAPI** that fetches country data from the [REST Countries API](https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies) and currency exchange rates from the [Open Exchange Rate API](https://open.er-api.com/v6/latest/USD). It stores this data in a MySQL database, computes estimated GDP, and exposes CRUD and analytical endpoints.

---

## ⚙️ Core Functionalities

* **Fetch and cache country data** from external APIs.
* **Compute estimated GDP** using population and exchange rate.
* **CRUD operations** for country records.
* **Filter and sort** by region, currency, or GDP.
* **Generate a summary image** of top 5 countries by GDP.
* **Provide system status** with total countries and last refresh timestamp.

---

## 🧱 Tech Stack

* **Backend:** FastAPI
* **Database:** MySQL
* **ORM:** SQLAlchemy
* **Environment Management:** python-dotenv
* **HTTP Client:** requests
* **Image Generation:** Pillow
* **Server:** Uvicorn / Hypercorn

---

## 🗂️ Database Schema

| Field             | Type         | Description                          |
| ----------------- | ------------ | ------------------------------------ |
| id                | Integer (PK) | Auto-generated                       |
| name              | String       | Country name (unique, required)      |
| capital           | String       | Optional                             |
| region            | String       | Optional                             |
| population        | Integer      | Required                             |
| currency_code     | String       | Required (nullable if not available) |
| exchange_rate     | Float        | Nullable                             |
| estimated_gdp     | Float        | Computed field                       |
| flag_url          | String       | Optional                             |
| last_refreshed_at | DateTime     | Auto timestamp                       |

---

## 🚀 Endpoints

### 1️⃣ **POST /countries/refresh**

Fetch countries and exchange rates, compute GDPs, and store in DB.

**Response:**

```json
{
  "message": "Data refreshed successfully",
  "total_countries": 250,
  "last_refreshed_at": "2025-10-22T18:00:00Z"
}
```

### 2️⃣ **GET /countries**

Fetch all cached countries.
Supports filters and sorting.

**Query Params:**

* `region=Africa`
* `currency=NGN`
* `sort=gdp_desc`

**Response:**

```json
[
  {
    "name": "Nigeria",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2
  }
]
```

### 3️⃣ **GET /countries/{name}**

Get one country by name.

**Response:**

```json
{
  "name": "Ghana",
  "capital": "Accra",
  "region": "Africa",
  "population": 31072940
}
```

### 4️⃣ **DELETE /countries/{name}**

Delete a country record.

**Response:**

```json
{"message": "Country deleted successfully"}
```

### 5️⃣ **GET /status**

Show total countries and last refresh time.

**Response:**

```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-22T18:00:00Z"
}
```

### 6️⃣ **GET /countries/image**

Serve the summary image.

**Response:** summary image (`cache/summary.png`) or:

```json
{"error": "Summary image not found"}
```

---

## 🧮 Estimated GDP Formula

```
estimated_gdp = (population × random(1000–2000)) ÷ exchange_rate
```

* Recomputed each refresh
* Random multiplier generated per country per refresh

---

## 🧾 Error Handling

| HTTP Code | Description           | Example                                           |
| --------- | --------------------- | ------------------------------------------------- |
| 400       | Validation failed     | `{ "error": "Validation failed" }`                |
| 404       | Not found             | `{ "error": "Country not found" }`                |
| 503       | External API failure  | `{ "error": "External data source unavailable" }` |
| 500       | Internal server error | `{ "error": "Internal server error" }`            |

---

## 🔐 Validation Rules

* `name`, `population`, and `currency_code` are required.
* Return 400 if validation fails.

---

## 🧰 Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone git@github.com:john-otienoh/CountryCurrencyExchangeAPI.git
cd CountryCurrencyAPI
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # (Linux/macOS)
venv\Scripts\activate      # (Windows)
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env` file

```bash
DB_URL=mysql+pymysql://user:password@localhost:3306/countrydb
BASE_CURRENCY=USD
PORT=8000
```

### 5️⃣ Run Migrations 

```bash
alembic upgrade head
```

### 6️⃣ Start Server

```bash
uvicorn main:app --reload
```

---


---

## 🧪 Testing

You can use `curl`, `Postman`, or `pytest` for endpoint validation.

**Example:**

```bash
curl -X POST https://yourapp.domain.app/countries/refresh
curl https://yourapp.domain.app/countries?region=Africa
```

---

## 📊 Summary Image

* Auto-generated on every refresh.
* Stored as `cache/summary.png`.
* Displays:

  * Total countries
  * Top 5 by estimated GDP
  * Last refresh timestamp

---

## 🧩 Submission Checklist

✅ API hosted and reachable
✅ README includes setup + env vars
✅ Correct response formats
✅ Summary image generated
✅ Refresh logic verified
