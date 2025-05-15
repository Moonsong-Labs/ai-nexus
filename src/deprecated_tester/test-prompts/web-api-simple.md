# ✅ Todo List Web API – Requirements & Interface

## 🔧 Business Requirements

### 1. Todo Management

1.1 Users can create new todo items.

### 2. Todo Features

2.1 Each todo must have a `title` and `status`.

---

## 📋 Todo Endpoints

### Create Todo

**POST** `//todos`

```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, and bread",
  "status": "pending"
}
```
