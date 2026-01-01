# 🍳 Recipe Share App - Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Python Requirements
```powershell
# Open PowerShell in the project directory
pip install -r requirements.txt
```

### Step 2: Run Setup
```powershell
python setup.py
```

This will:
- ✅ Create the `uploads` folder
- ✅ Initialize the SQLite database
- ✅ Create a test user (demo/demo1234)

### Step 3: Start the App
```powershell
python app.py
```

You should see:
```
Database initialized!
 * Running on http://127.0.0.1:5000
```

### Step 4: Open in Browser
- Go to **http://localhost:5000**
- You're ready to go! 🎉

---

## Default Test User

**Username:** demo  
**Password:** demo1234  
**Email:** demo@example.com  
**Role:** user (regular user)

---

## User Roles & Features

### 👤 User Role (Default - Regular Users)
Create and share recipes with the community

**Can Do:**
- ✅ Create new recipes with images
- ✅ Edit & delete own recipes
- ✅ Leave comments on recipes
- ✅ View own profile
- ✅ Change password
- ✅ Delete account

**Cannot Do:**
- ❌ Share PDF files
- ❌ Access admin panel

---

### 👨‍💼 Employee Role (Restaurant Staff)
Share secret restaurant recipes as PDFs

**Can Do:**
- ✅ Share PDF recipe files
- ✅ View & manage shared recipes
- ✅ Download own shared files
- ✅ Delete own shared files
- ✅ View employee dashboard
- ✅ Change password
- ✅ Delete account

**Cannot Do:**
- ❌ Create regular recipes
- ❌ Leave comments
- ❌ Access admin panel

**File Requirements:**
- 📄 PDF files only
- 📊 Max 16 MB per file
- 📝 Optional description

---

### 🔐 Admin Role (Administrator)
Manage employees and oversee system

**Can Do:**
- ✅ Access admin dashboard
- ✅ Create new employee accounts
- ✅ Edit employee username/email
- ✅ Reset employee username permissions
- ✅ View all shared PDF files (read-only)
- ✅ Change password
- ✅ Delete account

**Cannot Do:**
- ❌ Create recipes
- ❌ Download employee files
- ❌ Modify employee passwords directly
- ❌ Delete files (only employees can)

---

## Features Checklist

### ✅ User Management
- [x] Register with email
- [x] Login with password hashing
- [x] Failed login tracking (3 attempts = 15 min lockout)
- [x] Session handling (7 days)
- [x] User profile with role display
- [x] Change password functionality
- [x] Delete account (with data cleanup)

### ✅ Recipe Management (User Role)
- [x] Create new recipe (title, description, ingredients, instructions)
- [x] Edit recipes
- [x] Delete recipes
- [x] Difficulty levels (Easy/Medium/Hard)
- [x] Cooking time & servings

### ✅ Employee File Sharing
- [x] Share PDF recipes
- [x] Add description to shared files
- [x] View own shared files
- [x] Download own files
- [x] Delete own files
- [x] PDF-only validation
- [x] Secure filename generation

### ✅ Admin Management
- [x] Admin dashboard with statistics
- [x] Create employee accounts
- [x] Edit employee credentials
- [x] Track failed login attempts
- [x] Grant username reset permissions
- [x] View all shared files (read-only)

### ✅ Comments & Interaction
- [x] Leave comments on recipes
- [x] View comments with timestamps
- [x] User profile with stats

### ✅ Security
- [x] Password hashing (Argon2)
- [x] Password strength validation
- [x] Failed login attempt tracking
- [x] Account lockout (15 minutes)
- [x] CSRF protection ready
- [x] HTTPOnly cookies
- [x] Input validation
- [x] Path traversal prevention
- [x] PDF-only file validation for employees
- [x] Role-based access control

---

## Project Files

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application (all routes) |
| `models.py` | Database models (User, Recipe, Comment, SharedFile) |
| `config.py` | Configuration settings |
| `requirements.txt` | Python dependencies |
| `setup.py` | Setup script |
| `.env` | Environment variables |
| `templates/` | HTML templates (15 files) |
| `uploads/` | Uploaded files (auto-created) |

---

## Common Tasks

### For Regular Users

#### Create a Recipe
1. Login (or use demo/demo1234)
2. Click "+ New Recipe" in navigation
3. Fill in details:
   - Title (min 5 chars)
   - Description
   - Ingredients (one per line)
   - Instructions
   - Cooking time (optional)
   - Servings (optional)
   - Difficulty level
   - Image (optional)
4. Click "Create Recipe"

#### View & Comment on Recipes
- Home page shows all recipes
- Click "View Recipe" to see details
- Leave comments on any recipe (max 500 chars)

#### Manage Your Recipes
- Click "My Recipes" in navigation
- Edit or delete your recipes
- See comments and statistics

#### Change Password
- Click "Profile" in navigation
- Click "Change Password"
- Enter current password and new password
- New password must be strong (8+ chars)

#### Delete Account
- Click "Profile" in navigation
- Click "Delete Account" (at bottom)
- Enter password and type "DELETE" to confirm
- All recipes, comments, and files will be deleted

---

### For Employee Users

#### Share a Secret Recipe PDF
1. Click "Share Recipe" in navigation
2. Select your PDF file (max 16 MB)
3. Add a description (optional)
4. Click "Share Recipe"

#### Manage Shared Recipes
- Click "My Recipes" in navigation
- View all your shared PDFs
- Download any of your files
- Delete files you no longer need

#### Employee Dashboard
- Click "Dashboard" to see:
  - Total shared recipes count
  - Your role (Employee)
  - Member since date
  - Employee guidelines

---

### For Admin Users

#### Create New Employee
1. Click "Admin Panel" in navigation
2. Click "Create New Employee"
3. Set:
   - Username (min 3 chars)
   - Email
   - Initial password (must be strong)
4. Click "Create Employee"

#### Manage Employees
1. Go to "Admin Panel"
2. See list of all employees with status:
   - 🟢 Active
   - 🟠 Locked (after 3 failed login attempts)
   - 🟡 Username Reset Enabled
3. Click "Edit" to change username/email
4. Click "Reset Username" if employee is locked out

#### View All Shared Files
- Click "Shared Files" in navigation
- Browse all employee-shared PDFs
- View filename, employee, description, file size
- Admin cannot download or modify files
- Only employees can manage their own files

---

## Account Lockout & Recovery

### What Triggers Lockout?
- 3 failed login attempts within 15 minutes
- Account temporarily locked for 15 minutes

### How to Unlock?
**Option 1: Wait 15 Minutes**
- After 15 minutes, attempt counter resets
- You can login normally

**Option 2: Admin Reset**
- Admin grants "Reset Username" permission
- You then can reset your username
- Account unlock is automatic

---

## Configuration

Edit `config.py` to change:

```python
# Session timeout
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# File size limit (default: 16MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Allowed file types (general)
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx'}

# Allowed file types (employee PDF sharing)
EMPLOYEE_ALLOWED_EXTENSIONS = {'pdf'}
```

---

## Database

**Type:** SQLite (recipe_app.db)  
**Tables:** users, recipes, comments, shared_files

**New Fields:**
- `users.role` - user, employee, or admin
- `users.login_attempts` - failed login counter
- `users.last_login_attempt` - timestamp
- `users.username_reset_enabled` - admin reset flag

To reset database:
```powershell
Remove-Item recipe_app.db
python app.py
```

---

## Troubleshooting

### "ModuleNotFoundError"
```powershell
pip install -r requirements.txt
```

### "Account temporarily locked"
Wait 15 minutes or ask admin to grant username reset permission.

### "Account locked due to too many failed login attempts"
An admin needs to grant you username reset permission through the admin panel.

### "database is locked"
Close all other instances of the app and try again.

### File upload not working
Check that `uploads/` folder exists with write permissions.

### Can't login with demo user
Make sure you ran `setup.py` to create the test user.

### "Employees can only upload PDF files"
Make sure your file has `.pdf` extension and is actually a PDF.

---

## Password Requirements

All passwords must have:
- ✅ Minimum 8 characters
- ✅ Mix of uppercase and lowercase
- ✅ At least one number
- ✅ At least one special character (e.g., !@#$%)
- ✅ Not a common password (password, 1234, qwerty, etc.)

---

## Production Deployment

Before deploying to production:

1. **Change SECRET_KEY** in `.env`:
   ```
   SECRET_KEY=your-very-long-random-key-here
   ```

2. **Use production config** in `app.py`:
   ```python
   app.config.from_object(config['production'])
   ```

3. **Set HTTPS** and secure cookies

4. **Use a real database** (PostgreSQL, MySQL):
   ```python
   SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dbname'
   ```

5. **Use a production WSGI server**:
   ```powershell
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

6. **Enable CSRF Protection**:
   - Install Flask-WTF
   - Add CSRF tokens to all forms

---

## Support & Documentation

- Full routes: See `ROUTES.md`
- Project structure: See `STRUCTURE.md`
- Code comments: Review `app.py`
- Security info: See `README.md`

---

**Happy Recipe Sharing! 🍽️**

