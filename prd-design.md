# UTM-Based Tracking System — Product Design

## 1. Objective

Design a scalable tracking system that:

- Tracks link clicks across multiple channels (Email, WhatsApp, SMS, Telegram, etc.)
- Uses UTM parameters for flexible attribution
- Provides analytics without requiring strict channel registration

---

## 2. Core Concept

Instead of tightly coupling tracking with predefined channels, this system uses **UTM parameters**:

- utm_source → where traffic came from (whatsapp, email, sms)
- utm_medium → type of channel (chat, social, campaign)
- utm_campaign → campaign name or identifier

Example:

https://yourapp.com/t/abc123?utm_source=whatsapp&utm_medium=chat&utm_campaign=followup

---

## 3. High-Level Architecture

[Client / Dashboard / Extension]
        ↓
[Tracking API - FastAPI]
        ↓
[Redis Queue] → [Worker]
        ↓
[PostgreSQL DB]

User Flow:
User clicks link → /t/{code} → API logs → redirect

---

## 4. Tech Stack

| Layer        | Technology         |
|-------------|-------------------|
| API         | FastAPI (async)   |
| Database    | PostgreSQL        |
| Cache/Queue | Redis             |
| Worker      | Celery / RQ       |
| Deployment  | Docker + Kubernetes |

---

## 5. Data Model

### 5.1 Tracking Links

| Field         | Type    | Description |
|--------------|--------|-------------|
| link_id      | UUID   | Unique ID |
| short_code   | string | URL slug (abc123) |
| original_url | string | Destination URL |
| created_at   | timestamp | Creation time |

---

### 5.2 Click Events

| Field         | Type      | Description |
|--------------|----------|-------------|
| id           | PK       | |
| link_id      | FK       | |
| clicked_at   | timestamp| |
| ip           | string   | |
| user_agent   | string   | |
| utm_source   | string   | optional |
| utm_medium   | string   | optional |
| utm_campaign | string   | optional |

---

## 6. API Contracts

---

### 6.1 Create Tracking Link

POST /links

Request:
{
  "original_url": "https://example.com"
}

Response:
{
  "link_id": "uuid",
  "tracking_url": "https://yourapp.com/t/abc123"
}

---

### 6.2 Redirect & Track Click

GET /t/{short_code}

Optional query params:
- utm_source
- utm_medium
- utm_campaign

Example:
GET /t/abc123?utm_source=whatsapp&utm_campaign=promo

---

### Behavior:

1. Resolve short_code → original_url  
2. Extract UTM parameters  
3. Capture metadata:
   - IP
   - User-Agent
   - Timestamp  
4. Push event to Redis queue  
5. Redirect (HTTP 302) → original_url  

---

### 6.3 Get Link Analytics

GET /links/{link_id}/stats

Response:
{
  "link_id": "uuid",
  "total_clicks": 100,
  "unique_clicks": 75,
  "by_source": {
    "whatsapp": 40,
    "email": 30,
    "sms": 30
  },
  "by_campaign": {
    "promo": 60,
    "followup": 40
  }
}

---

### 6.4 Bulk Analytics

POST /links/stats

Request:
{
  "link_ids": ["id1", "id2"]
}

---

## 7. Event Processing Strategy

Problem:
High traffic from clicks.

Solution:

1. API writes click events → Redis queue  
2. Worker consumes → writes to DB  

Flow:
[API] → [Redis] → [Worker] → [DB]

Benefits:
- Fast redirects
- Scalable ingestion
- Reduced DB load

---

## 8. UTM Handling Strategy

### Priority Order:

1. Query parameters (utm_source, utm_medium, utm_campaign)
2. Fallback: NULL

---

### Example Mapping:

| URL | Stored Data |
|-----|------------|
| /t/abc123?utm_source=whatsapp | utm_source = whatsapp |
| /t/abc123 | utm_source = NULL |

---

## 9. Analytics Capabilities

System supports:

- Click count
- Unique users (based on IP + User-Agent)
- Source breakdown (utm_source)
- Campaign breakdown (utm_campaign)

---

## 10. Advantages of UTM-Based Design

### ✅ Flexible
- No need to predefine channels

### ✅ Works everywhere
- Email, WhatsApp, SMS, Telegram

### ✅ Industry standard
- Compatible with marketing tools

### ✅ Lightweight
- No mandatory campaign creation

---

## 11. Limitations

- UTM depends on user input
- Missing UTM → limited attribution
- IP-based uniqueness is approximate

---

## 12. Scaling Considerations

- Indexes:
  - link_id
  - utm_source
  - clicked_at
- Partition click_events by date (future)
- Use Redis buffering for burst traffic

---

## 13. Future Enhancements

- Auto-detect channel (via User-Agent)
- Geo-location tracking
- Device analytics
- Link expiration
- Dashboard UI
- Real-time analytics (WebSocket)

---

## 14. Key Insight

UTM-based tracking separates:

Tracking → system responsibility  
Attribution → user-controlled  

This makes the system flexible and scalable.

---

## 15. Summary

| Feature | Method |
|--------|--------|
| Tracking | Redirect endpoint |
| Attribution | UTM parameters |
| Storage | PostgreSQL |
| Performance | Redis queue |
| Backend | FastAPI |