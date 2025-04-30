# ✅ Todo List Web API – Requirements & Interface

## 🔧 Business Requirements

### 1. Todo Management

1.1 Users can create new todo items.  
1.2 Users can view a list of all todos.  
1.3 Users can view a single todo by ID.  
1.4 Users can update existing todo items.  
1.5 Users can delete todo items.

### 2. Todo Features

2.1 Each todo must have a `title` and `status`.  
2.2 Todos may include an optional `description`.  
2.3 Users can filter todos by `status`.
2.4 Todos status can be `pending`, `in progress`, or `completed`.

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

---

### List Todos

**GET** `/todos`

**Query Parameters (optional):**

```
?status=pending
```

---

### View Todo

**GET** `/todos/{id}`

---

### Update Todo

**PUT** `/todos/{id}`

```json
{
  "status": "completed",
  "description": "Got everything from the store"
}
```

---

### Delete Todo

**DELETE** `/todos/{id}`
