# Recipe Share App - Complete Route Reference

## Public Routes (No Login Required)

### Home & Discovery
- **GET `/`**
  - Home page with all recipes
  - Paginated (6 per page)
  - Browse recipes from all users

### Authentication
- **GET `/register`**
  - Registration form
  - Field validation (username 3+, password 8+, unique email)
  - Creates users with 'user' role by default
  
- **POST `/register`**
  - Submit registration
  - Creates user with hashed password
  - Redirects to login on success

- **GET `/login`**
  - Login form
  - Remember me checkbox
  - Tracks failed login attempts
  - Account locks after 3 failed attempts (15 minutes)

- **POST `/login`**
  - Authenticate user
  - Creates session (7-day timeout)
  - Records failed login attempts
  - Locks account if 3 failed attempts
  - Supports "next" parameter for redirects

### Recipe Details
- **GET `/recipe/<recipe_id>`**
  - View full recipe details
  - See all comments
  - User info and recipe metadata

### File Downloads
- **GET `/upload/<filename>`**
  - Download uploaded files
  - Security: filename sanitization
  - Path traversal prevention

---

## Protected Routes (Login Required)

### Authentication
- **GET `/logout`**
  - Destroy user session
  - Redirect to home

### User Profile & Account Management
- **GET `/profile`**
  - View user profile and stats
  - Recipe/file count
  - Comment count
  - Member since date
  - Account status display
  - Role badge (User/Employee/Admin)

- **GET `/change-password`**
  - Change password form
  - Current password verification required

- **POST `/change-password`**
  - Update user password
  - Validates current password
  - Validates password strength
  - Redirects to profile on success

- **GET `/delete-account`**
  - Account deletion confirmation page
  - Shows what will be deleted
  - Requires password & DELETE confirmation

- **POST `/delete-account`**
  - Permanently delete user account
  - Deletes all recipes and uploaded files
  - Deletes all comments
  - Requires password verification
  - Logs out user after deletion

---

## Recipe Management (User Role Only)

### Recipe CRUD
- **GET `/recipe/new`**
  - Create recipe form
  - Multipart form (file upload)

- **POST `/recipe/new`**
  - Create new recipe
  - Process file upload
  - Validate all fields
  - Redirect to recipe view

- **GET `/recipe/<recipe_id>/edit`**
  - Edit recipe form (author only)
  - Show current recipe data
  - Display existing image

- **POST `/recipe/<recipe_id>/edit`**
  - Update recipe details (author only)
  - Optional new image upload
  - Update timestamp

- **POST `/recipe/<recipe_id>/delete`**
  - Delete recipe (author only)
  - Remove uploaded image
  - Delete all comments

### User Recipe List
- **GET `/my-recipes`**
  - View user's recipes only
  - Paginated (6 per page)
  - Edit/delete buttons visible

### Comments
- **POST `/recipe/<recipe_id>/comment`**
  - Add comment to recipe
  - Max 500 characters
  - Must be logged in

---

## Admin Routes (Admin Role Only)

### Admin Dashboard & Management
- **GET `/admin/dashboard`**
  - Admin dashboard with statistics
  - Total users count
  - Total employees count
  - Employee list with status
  - Quick action buttons

- **GET `/admin/create-employee`**
  - Create new employee account form
  - Username, email, password required

- **POST `/admin/create-employee`**
  - Create employee account
  - Sets role to 'employee'
  - Validates password strength
  - Checks for duplicate username/email
  - Redirects to admin dashboard

- **GET `/admin/edit-employee/<employee_id>`**
  - Edit employee details form
  - Can update username and email only

- **POST `/admin/edit-employee/<employee_id>`**
  - Update employee username/email
  - Password cannot be changed by admin
  - Employee changes password through their profile
  - Validates uniqueness of new credentials

- **POST `/admin/reset-username/<employee_id>`**
  - Grant username reset permission
  - Only if employee has 3+ failed login attempts
  - Resets login attempt counter
  - Enables username_reset_enabled flag

- **GET `/admin/view-shared-files`**
  - View-only access to all shared files
  - Paginated (10 per page)
  - Shows filename, employee, description, size, upload date
  - Admin cannot download or modify files

---

## Employee Routes (Employee Role Only)

### Employee Dashboard & File Sharing
- **GET `/employee/dashboard`**
  - Employee dashboard
  - Shared recipes count
  - Role display
  - Member since date
  - Quick action buttons
  - Employee guidelines

- **GET `/employee/share-file`**
  - Share PDF recipe form
  - File upload (PDF only)
  - Optional description field

- **POST `/employee/share-file`**
  - Upload PDF recipe
  - Validates PDF-only file type
  - Stores with secure filename
  - Tracks original filename, size
  - Redirects to employee's files list

- **GET `/employee/my-files`**
  - View employee's shared files
  - Paginated (10 per page)
  - Shows filename, description, size, upload date
  - Download and delete buttons

- **GET `/employee/download-file/<file_id>`**
  - Download own uploaded PDF
  - Employee ownership verification
  - Downloads with original filename

- **POST `/employee/delete-file/<file_id>`**
  - Delete own shared file
  - Employee ownership verification
  - Marks file as inactive (audit trail)
  - Removes physical file from storage

---

## Error Handlers

- **404 Not Found** - `/templates/404.html`
- **500 Server Error** - `/templates/500.html`

---

## Form Fields by Endpoint

### POST /register
```
username (required, min 3)
email (required, valid email)
password (required, min 8)
confirm_password (required, min 8)
```

### POST /login
```
username (required)
password (required)
remember (optional checkbox)
```

### POST /change-password
```
current_password (required)
new_password (required, min 8)
confirm_password (required, min 8)
```

### POST /delete-account
```
password (required)
confirm_delete (required, must be "DELETE")
```

### POST /recipe/new
```
title (required, min 5)
description (required)
ingredients (required, multiline)
instructions (required, multiline)
cooking_time (optional, integer)
servings (optional, integer)
difficulty (optional, default "Medium")
image (optional, file upload)
```

### POST /recipe/<id>/edit
```
title (required, min 5)
description (required)
ingredients (required, multiline)
instructions (required, multiline)
cooking_time (optional, integer)
servings (optional, integer)
difficulty (optional)
image (optional, file upload)
```

### POST /recipe/<id>/comment
```
content (required, max 500)
```

### POST /admin/create-employee
```
username (required, min 3)
email (required, valid email)
password (required, min 8, strong)
confirm_password (required, min 8)
```

### POST /admin/edit-employee/<id>
```
username (required, min 3)
email (required, valid email)
```

### POST /employee/share-file
```
description (optional, text)
file (required, PDF only, max 16MB)
```

---

## Response Codes & Redirects

| Route | Method | Success | Redirect |
|-------|--------|---------|----------|
| /register | POST | 302 | /login |
| /login | POST | 302 | /recipe/new (next param) or / |
| /logout | GET | 302 | / |
| /change-password | POST | 302 | /profile |
| /delete-account | POST | 302 | / |
| /recipe/new | POST | 302 | /recipe/{id} |
| /recipe/{id}/edit | POST | 302 | /recipe/{id} |
| /recipe/{id}/delete | POST | 302 | /my-recipes |
| /recipe/{id}/comment | POST | 302 | /recipe/{id} |
| /admin/dashboard | GET | 200 | - |
| /admin/create-employee | POST | 302 | /admin/dashboard |
| /admin/edit-employee/{id} | POST | 302 | /admin/dashboard |
| /admin/reset-username/{id} | POST | 302 | /admin/dashboard |
| /employee/share-file | POST | 302 | /employee/my-files |
| /employee/delete-file/{id} | POST | 302 | /employee/my-files |

---

## HTTP Methods Used

| Method | Purpose |
|--------|---------|
| GET | Display pages, download files |
| POST | Submit forms, authentication, create/update data |

*Note: DELETE method not used (uses POST with hidden method parameter for CSRF compatibility)*

---

## Query Parameters

- **`page`** - Pagination (index, my-recipes, my-files, view-shared-files)
  - Example: `/?page=2`

- **`next`** - Redirect after login
  - Example: `/login?next=/recipe/new`

---

## Flash Messages

Flash messages are used for user feedback:

| Type | Message |
|------|---------|
| success | Account created, recipe saved, file shared, etc. |
| danger | Validation errors, permission errors, locked account |
| warning | Failed login attempts, temporary lockout |
| info | Logout message |

Messages auto-dismiss with Bootstrap alert close button.

---

## Security Features per Route

### Authentication Routes
- ✅ Password validation (min 8 chars, strong)
- ✅ Password hashing (Argon2)
- ✅ Duplicate username/email check
- ✅ Session timeout (7 days)
- ✅ HTTPOnly cookies
- ✅ Failed login attempt tracking
- ✅ Account lockout after 3 failed attempts (15 min)
- ✅ Common password blacklist

### Recipe Routes
- ✅ Login required (except view)
- ✅ Author authorization check (edit/delete)
- ✅ Input validation & sanitization
- ✅ CSRF ready (implement form tokens)

### Admin Routes
- ✅ Admin role required
- ✅ View-only access to files (no download/modify)
- ✅ Employee creation with strong password
- ✅ Username/email edit with duplicate check
- ✅ Failed login tracking visibility

### Employee Routes
- ✅ Employee role required
- ✅ PDF-only file upload validation
- ✅ Ownership verification (can only manage own files)
- ✅ Secure filename generation
- ✅ File size limit (16MB)
- ✅ Path traversal prevention

### User Account Management
- ✅ Current password verification for changes
- ✅ Strong password confirmation
- ✅ Explicit deletion confirmation (type "DELETE")
- ✅ Audit trail (soft delete for shared files)

---

## Role-Based Access Control (RBAC)

### User Role (Default)
- ✅ Create, read, edit, delete recipes
- ✅ Comment on recipes
- ✅ View profile
- ✅ Change password
- ✅ Delete account
- ❌ Access admin panel
- ❌ Share PDF files

### Employee Role
- ✅ View dashboard
- ✅ Share PDF recipes only
- ✅ Manage own shared files
- ✅ Download own files
- ✅ Change password
- ✅ Delete account
- ❌ Create regular recipes
- ❌ Comment on recipes
- ❌ Access admin panel

### Admin Role
- ✅ Access admin dashboard
- ✅ Create new employees
- ✅ Edit employee credentials (username/email)
- ✅ Reset username permission
- ✅ View all shared files (read-only)
- ✅ Change password
- ✅ Delete account
- ❌ Create recipes
- ❌ Download employee files
- ❌ Modify employee files

---

## Pagination Configuration

| Route | Items Per Page |
|-------|---|
| Home page | 6 |
| My Recipes | 6 |
| My Files | 10 |
| View Shared Files | 10 |

---

## File Upload Configuration

| Setting | Value |
|---------|-------|
| Max Size | 16MB |
| Storage | `uploads/` folder |
| Naming | Random hex + extension |
| Allowed Types (General) | pdf, txt, jpg, jpeg, png, gif, doc, docx |
| Allowed Types (Employee) | pdf only |

---

## Database Model Fields

### User Model
```
id (Integer, Primary Key)
username (String, Unique)
email (String, Unique)
password_hash (String)
role (String) - 'user', 'employee', or 'admin'
created_at (DateTime)
updated_at (DateTime)
login_attempts (Integer) - failed login counter
last_login_attempt (DateTime)
username_reset_enabled (Boolean)
```

### SharedFile Model
```
id (Integer, Primary Key)
filename (String) - secure random name
original_filename (String) - user's original filename
description (Text)
file_size (Integer) - in bytes
created_at (DateTime)
updated_at (DateTime)
is_active (Boolean) - soft delete flag
user_id (Integer, Foreign Key) - employee who uploaded
```

---

## Database Relationships

```
User (1) ──────────→ (N) Recipe
  ↓                   ↓
  └─→ (N) Comment ←──┘

User (1) ──────────→ (N) SharedFile
```

---

## Template Variables Passed

### base.html (All templates)
- `current_user` - Flask-Login user object with role

### index.html
- `recipes` - Paginated recipe query

### view_recipe.html
- `recipe` - Recipe object
- `comments` - Comment list

### my_recipes.html
- `recipes` - User's paginated recipes

### profile.html
- `recipe_count` - Integer
- `comment_count` - Integer

### admin_dashboard.html
- `employees` - List of employee objects
- `user_count` - Total users
- `employee_count` - Total employees

### admin_view_shared_files.html
- `shared_files` - Paginated shared files

### employee_dashboard.html
- `files_count` - Employee's shared files count

### employee_my_files.html
- `shared_files` - Paginated employee's files

---

## URL Structure Examples

```
http://localhost:5000/                          # Home
http://localhost:5000/register                  # Register
http://localhost:5000/login                     # Login
http://localhost:5000/logout                    # Logout
http://localhost:5000/profile                   # Profile
http://localhost:5000/change-password           # Change password
http://localhost:5000/delete-account            # Delete account
http://localhost:5000/recipe/1                  # View recipe 1
http://localhost:5000/recipe/new                # Create recipe
http://localhost:5000/recipe/1/edit             # Edit recipe 1
http://localhost:5000/recipe/1/delete           # Delete recipe 1
http://localhost:5000/recipe/1/comment          # Add comment to recipe 1
http://localhost:5000/upload/abc123def.jpg      # Download image
http://localhost:5000/my-recipes                # My recipes
http://localhost:5000/admin/dashboard           # Admin dashboard
http://localhost:5000/admin/create-employee     # Create employee
http://localhost:5000/admin/edit-employee/5    # Edit employee 5
http://localhost:5000/admin/reset-username/5   # Reset username for employee 5
http://localhost:5000/admin/view-shared-files   # View all shared files
http://localhost:5000/employee/dashboard        # Employee dashboard
http://localhost:5000/employee/share-file       # Share PDF
http://localhost:5000/employee/my-files         # My shared files
http://localhost:5000/employee/delete-file/3    # Delete shared file 3
http://localhost:5000/employee/download-file/3  # Download shared file 3
```

---

## Session & Cookie Information

**Session Duration:** 7 days  
**Cookie Name:** `session`  
**Cookie Flags:**
- HttpOnly: ✅ (prevents XSS)
- Secure: ❌ (local dev), ✅ (production)
- SameSite: Lax (prevents CSRF)

**Account Lockout:** 3 failed login attempts → 15 minute lockout

---

## Decorators & Authorization

All protected routes use the `@login_required` decorator.

Admin and Employee routes use the custom `@require_role(role)` decorator:
```python
@require_role(UserRole.ADMIN.value)   # Admin only
@require_role(UserRole.EMPLOYEE.value)  # Employee only
```

---

**Last Updated:** January 2026  
**Framework:** Flask 2.3.3  
**Auth:** Flask-Login 0.6.2  
**Database:** SQLAlchemy 3.0.3

