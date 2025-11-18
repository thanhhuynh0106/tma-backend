# API Testing Guide

Hướng dẫn test API cho tất cả các apps trong hệ thống.

## Base URL
```
http://localhost:8000
```

## Authentication

Hầu hết các endpoints yêu cầu JWT token trong header:
```
Authorization: Bearer <access_token>
```

Để lấy token, đăng nhập qua `/api/auth/login/`

---

## 1. Authentication API

### 1.1 Register
**POST** `/api/auth/register/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "employee",
  "profile": {
    "fullName": "Nguyen Van A",
    "employeeID": "EMP001",
    "phone": "0123456789",
    "department": "IT",
    "position": "Developer"
  },
  "teamId": "team_id_here",
  "managerId": "manager_id_here"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {...},
    "tokens": {
      "access": "...",
      "refresh": "..."
    }
  }
}
```

### 1.2 Login
**POST** `/api/auth/login/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 1.3 Change Password
**POST** `/api/auth/change-password/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "user_id": "user_id_here",
  "current_password": "old_password",
  "new_password": "new_password123"
}
```

---

## 2. Users API

### 2.1 List Users
**GET** `/api/users/`
**Auth Required:** Yes

**Query Params:**
- `page=1` (optional)
- `page_size=20` (optional)
- `role=employee` (optional)
- `team_id=team_id` (optional)

### 2.2 Get Current User
**GET** `/api/users/me/`
**Auth Required:** Yes

### 2.3 Get User Detail
**GET** `/api/users/<user_id>/`
**Auth Required:** Yes

### 2.4 Update User
**PUT** `/api/users/<user_id>/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "profile": {
    "fullName": "Updated Name",
    "phone": "0987654321"
  },
  "role": "team_lead"
}
```

### 2.5 Create User
**POST** `/api/users/`
**Auth Required:** Yes

**Request Body:** (Same as Register)

---

## 3. Leaves API

### 3.1 Create Leave Request
**POST** `/api/leaves/`
**Auth Required:** No

**Request Body:**
```json
{
  "user_id": "691b6e59dfbf86ce69255714",
  "type": "vacation",
  "start_date": "2024-12-20T00:00:00Z",
  "end_date": "2024-12-25T00:00:00Z",
  "number_of_days": 5,
  "reason": "Family vacation"
}
```

**Leave Types:** `vacation`, `sick`, `personal`

### 3.2 List Leaves
**GET** `/api/leaves/`
**Auth Required:** No

**Query Params:**
- `page=1`
- `page_size=20`
- `user_id=user_id` (optional)
- `status=pending` (optional: `pending`, `approved`, `rejected`)

### 3.3 Get My Leaves
**GET** `/api/leaves/me/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`
- `status=pending` (optional)

### 3.4 Get Leave Detail
**GET** `/api/leaves/<leave_id>/`
**Auth Required:** Yes

### 3.5 Update Leave
**PUT** `/api/leaves/<leave_id>/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "start_date": "2024-12-21T00:00:00Z",
  "end_date": "2024-12-26T00:00:00Z",
  "number_of_days": 6,
  "reason": "Updated reason"
}
```

**Note:** Chỉ có thể update khi `status = "pending"`

### 3.6 Approve Leave
**PUT** `/api/leaves/<leave_id>/approve/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "approver_id": "approver_user_id"
}
```

**Note:** Có thể để trống `approver_id` để dùng `request.user`

### 3.7 Reject Leave
**PUT** `/api/leaves/<leave_id>/reject/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "approver_id": "approver_user_id",
  "reason": "Insufficient leave balance"
}
```

**Note:** `reason` là bắt buộc

---

## 4. Tasks API

### 4.1 Create Task
**POST** `/api/tasks/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the project",
  "status": "todo",
  "priority": "high",
  "team_id": "team_id_here",
  "assigned_to": ["user_id_1", "user_id_2"],
  "assigned_by_id": "user_id_here",
  "start_date": "2024-12-20T00:00:00Z",
  "due_date": "2024-12-25T00:00:00Z",
  "progress": 0,
  "tags": ["documentation", "important"],
  "attachments": [
    {
      "name": "doc.pdf",
      "url": "https://example.com/doc.pdf"
    }
  ]
}
```

**Note:** 
- `assigned_to`: Array of user IDs (có thể dùng `assigned_to_ids` thay thế)
- `assigned_by_id`: Optional, nếu không có sẽ dùng `request.user` (nếu authenticated)

**Status:** `todo`, `in_progress`, `completed`, `cancelled`
**Priority:** `low`, `medium`, `high`

### 4.2 List Tasks
**GET** `/api/tasks/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`
- `status=todo` (optional)
- `team_id=team_id` (optional)
- `assigned_to=user_id` (optional)

### 4.3 Get Task Detail
**GET** `/api/tasks/<task_id>/`
**Auth Required:** Yes

### 4.4 Update Task
**PUT** `/api/tasks/<task_id>/`
**Auth Required:** Yes

**Request Body:** (Partial update)
```json
{
  "status": "in_progress",
  "progress": 50
}
```

### 4.5 Change Task Status
**PUT** `/api/tasks/<task_id>/status/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "status": "completed"
}
```

### 4.6 Add Comment to Task
**POST** `/api/tasks/<task_id>/comment/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "text": "This task is almost done",
  "user_id": "user_id_here"
}
```

**Note:** Có thể để trống `user_id` để dùng `request.user`

### 4.7 Add Attachment to Task
**POST** `/api/tasks/<task_id>/attachment/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "attachment": {
    "name": "file.pdf",
    "url": "https://example.com/file.pdf"
  }
}
```

### 4.8 Delete Task
**DELETE** `/api/tasks/<task_id>/`
**Auth Required:** Yes

---

## 5. Teams API

### 5.1 Create Team
**POST** `/api/teams/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "name": "Development Team",
  "description": "Main development team",
  "leader_id": "leader_user_id",
  "member_ids": ["user_id_1", "user_id_2", "user_id_3"]
}
```

### 5.2 List Teams
**GET** `/api/teams/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`

### 5.3 Get Team Detail
**GET** `/api/teams/<team_id>/`
**Auth Required:** Yes

### 5.4 Update Team
**PUT** `/api/teams/<team_id>/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "name": "Updated Team Name",
  "description": "Updated description",
  "leader_id": "new_leader_id",
  "member_ids": ["user_id_1", "user_id_2"]
}
```

### 5.5 Add Member to Team
**POST** `/api/teams/<team_id>/members/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "user_id": "user_id_to_add"
}
```

### 5.6 Remove Member from Team
**DELETE** `/api/teams/<team_id>/members/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "user_id": "user_id_to_remove"
}
```

### 5.7 Delete Team
**DELETE** `/api/teams/<team_id>/`
**Auth Required:** Yes

---

## 6. Attendance API

### 6.1 Clock In
**POST** `/api/attendance/clock-in/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "user_id": "user_id_here",
  "location": {
    "lat": 10.762622,
    "lng": 106.660172
  }
}
```

**Note:** Có thể để trống `user_id` để dùng `request.user`

### 6.2 Clock Out
**POST** `/api/attendance/clock-out/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "user_id": "user_id_here"
}
```

**Note:** Có thể để trống `user_id` để dùng `request.user`

### 6.3 List Attendance
**GET** `/api/attendance/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`
- `user_id=user_id` (optional)
- `start_date=2024-12-01` (optional, format: YYYY-MM-DD)
- `end_date=2024-12-31` (optional, format: YYYY-MM-DD)

### 6.4 Get My Attendance Records
**GET** `/api/attendance/me/`
**Auth Required:** Yes

**Description:** Lấy tất cả attendance records của user hiện tại (authenticated user)

**Query Params:**
- `page=1`
- `page_size=20`
- `start_date=2024-12-01` (optional, format: YYYY-MM-DD)
- `end_date=2024-12-31` (optional, format: YYYY-MM-DD)

**Example:**
```
GET /api/attendance/me/?page=1&page_size=20&start_date=2024-12-01&end_date=2024-12-31
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "attendance_id",
      "user": "user_id",
      "date": "2024-12-19",
      "clock_in": "2024-12-19T07:30:00Z",
      "clock_out": "2024-12-19T17:30:00Z",
      "location": {
        "lat": 10.870000,
        "lng": 106.803000
      },
      "status": "present",
      "work_hours": 10.0,
      "created_at": "2024-12-19T07:30:00Z",
      "updated_at": "2024-12-19T17:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 6.5 Get User Attendance Records
**GET** `/api/attendance/user/<user_id>/`
**Auth Required:** Yes

**Description:** Lấy tất cả attendance records của một user cụ thể (dùng cho admin/manager để xem attendance của nhân viên)

**Query Params:**
- `page=1`
- `page_size=20`
- `start_date=2024-12-01` (optional, format: YYYY-MM-DD)
- `end_date=2024-12-31` (optional, format: YYYY-MM-DD)

**Example:**
```
GET /api/attendance/user/691ca1dd1c2887e9240d5531/?page=1&page_size=20
```

**Response:** Tương tự như 6.4

### 6.6 Get Attendance Detail
**GET** `/api/attendance/<attendance_id>/`
**Auth Required:** Yes

### 6.7 Update Attendance
**PUT** `/api/attendance/<attendance_id>/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "location": {
    "lat": 10.762622,
    "lng": 106.660172
  },
  "status": "late"
}
```

**Status:** `present`, `late`, `absent`

### 6.8 Delete Attendance
**DELETE** `/api/attendance/<attendance_id>/`
**Auth Required:** Yes

---

## 7. Conversations API

### 7.1 Create Conversation
**POST** `/api/conversations/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "participant_ids": ["user_id_1", "user_id_2", "user_id_3"]
}
```

**Note:** Cần ít nhất 2 participants

### 7.2 List Conversations
**GET** `/api/conversations/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`
- `user_id=user_id` (optional, default: current user)

### 7.3 Get Conversation Detail
**GET** `/api/conversations/<conversation_id>/`
**Auth Required:** Yes

### 7.4 Update Conversation
**PUT** `/api/conversations/<conversation_id>/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "participant_ids": ["user_id_1", "user_id_2"],
  "unread_count": {
    "user_id_1": 5,
    "user_id_2": 3
  }
}
```

### 7.5 Delete Conversation
**DELETE** `/api/conversations/<conversation_id>/`
**Auth Required:** Yes

---

## 8. Messages API

### 8.1 Send Message
**POST** `/api/messages/conversations/<conversation_id>/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "sender_id": "sender_user_id",
  "message": "Hello, how are you?",
  "attachments": [
    {
      "name": "image.jpg",
      "url": "https://example.com/image.jpg"
    }
  ]
}
```

**Note:** Có thể để trống `sender_id` để dùng `request.user`

### 8.2 List Messages in Conversation
**GET** `/api/messages/conversations/<conversation_id>/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`

### 8.3 Get Message Detail
**GET** `/api/messages/<message_id>/`
**Auth Required:** Yes

### 8.4 Mark Message as Read
**PUT** `/api/messages/<message_id>/read/`
**Auth Required:** Yes

### 8.5 Delete Message
**DELETE** `/api/messages/<message_id>/`
**Auth Required:** Yes

---

## 9. Notifications API

### 9.1 Create Notification
**POST** `/api/notifications/`
**Auth Required:** Yes

**Request Body:**
```json
{
  "user_id": "user_id_here",
  "type": "task_assigned",
  "title": "New Task Assigned",
  "message": "You have been assigned a new task",
  "related_id": "task_id_here",
  "is_read": false
}
```

**Types:** `task_assigned`, `leave_approved`, `leave_rejected`, `message_received`, `attendance_reminder`, etc.

### 9.2 List Notifications
**GET** `/api/notifications/`
**Auth Required:** Yes

**Query Params:**
- `page=1`
- `page_size=20`
- `user_id=user_id` (optional, default: current user)
- `unread_only=true` (optional, default: false)

### 9.3 Get Notification Detail
**GET** `/api/notifications/<notification_id>/`
**Auth Required:** Yes

### 9.4 Mark Notification as Read
**PUT** `/api/notifications/<notification_id>/read/`
**Auth Required:** Yes

### 9.5 Delete Notification
**DELETE** `/api/notifications/<notification_id>/`
**Auth Required:** Yes

---

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": {...},
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message here"
}
```

---

## Postman Collection Variables

Tạo các variables sau trong Postman:

```
base_url: http://localhost:8000
access_token: <your_access_token>
user_id: <your_user_id>
team_id: <your_team_id>
conversation_id: <conversation_id>
task_id: <task_id>
leave_id: <leave_id>
```

---

## Testing Flow Example

1. **Register/Login** → Lấy access_token
2. **Get Current User** → Lấy user_id
3. **Create Team** → Lấy team_id
4. **Create Task** → Lấy task_id
5. **Create Leave Request** → Lấy leave_id
6. **Approve/Reject Leave** → Test approval flow
7. **Clock In/Out** → Test attendance
8. **Create Conversation** → Lấy conversation_id
9. **Send Message** → Test messaging
10. **Create Notification** → Test notifications

---

## Notes

- Tất cả datetime fields sử dụng ISO 8601 format: `2024-12-20T00:00:00Z`
- Date fields sử dụng format: `2024-12-20`
- ObjectId fields là strings: `"691b6e59dfbf86ce69255714"`
- Pagination mặc định: `page=1`, `page_size=20`
- Nếu không có `user_id` trong request body, hệ thống sẽ dùng `request.user.id` (nếu authenticated)

