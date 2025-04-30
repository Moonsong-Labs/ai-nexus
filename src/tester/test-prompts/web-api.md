# ✅ Todo List Web API – Requirements & Interface

## 🔧 Business Requirements

### 1. User Management

1.1 Users can register with name and email.  
1.2 Users receive a unique user ID upon registration.  
1.3 Users can update their name or email.  
1.4 Users can delete their accounts.

### 2. Todo Management

2.1 Users can create new todo items.  
2.2 Users can view a list of all their todos.  
2.3 Users can view a single todo by ID.  
2.4 Users can update existing todo items.  
2.5 Users can delete todo items.

### 3. Todo Features

3.1 Each todo must have a `title` and `status`.  
3.2 Todos may include an optional `description`.  
3.3 Todos may include an optional `deadline` (ISO 8601 format).  
3.4 Todos can have zero or more `tags`.  
3.5 Users can filter todos by `status`, `tag`, and `deadline`.

---

## 🧑‍💻 User Endpoints

### Register

**POST** `/users`

```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Response:**

```json
{
  "user_id": "abc123"
}
```

---

### Update User

**PUT** `/users/{user_id}`

```json
{
  "name": "Johnny",
  "email": "johnny@example.com"
}
```

---

### Delete User

**DELETE** `/users/{user_id}`

---

## 📋 Todo Endpoints

### Create Todo

**POST** `/users/{user_id}/todos`

```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, and bread",
  "status": "pending",
  "deadline": "2025-05-10T17:00:00Z",
  "tags": ["shopping", "urgent"]
}
```

---

### List Todos

**GET** `/users/{user_id}/todos`

**Query Parameters (optional):**

```
?status=pending&tag=shopping&due_before=2025-05-10
```

---

### View Todo

**GET** `/users/{user_id}/todos/{id}`

---

### Update Todo

**PUT** `/users/{user_id}/todos/{id}`

```json
{
  "status": "completed",
  "description": "Got everything from the store"
}
```

---

### Delete Todo

**DELETE** `/users/{user_id}/todos/{id}`
