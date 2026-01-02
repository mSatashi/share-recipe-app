from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from models import db, User, Recipe, Comment, SharedFile, UserRole
from config import config
import os
from datetime import datetime
from functools import wraps
import secrets

app = Flask(__name__)
app.config.from_object(config['development'])

csrf = CSRFProtect(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_employee_file(filename):
    """Check if file is allowed for employee uploads (PDF only)"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['EMPLOYEE_ALLOWED_EXTENSIONS']

def secure_upload_file(file, is_employee=False):
    """Sanitize and secure file upload"""
    if not file or file.filename == '':
        return None
    
    if is_employee:
        if not is_employee_file(file.filename):
            raise ValueError("Employees can only upload PDF files")
    else:
        if not allowed_file(file.filename):
            raise ValueError(f"File type not allowed. Allowed: {', '.join(app.config['ALLOWED_EXTENSIONS'])}")
    
    # Generate random filename to prevent directory traversal
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secrets.token_hex(16) + '.' + ext
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return filename

def require_role(role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in first.', 'danger')
                return redirect(url_for('login'))
            
            if not current_user.has_role(role):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def evaluate_password_server(pw):
    """Evaluate password strength on the server side. Returns (score, recommendations).
    Score is normalized 0..4 (higher is better)."""
    recommendations = []
    score = 0
    if not pw:
        return 0, ["Enter a password"]

    if len(pw) >= 8:
        score += 1
    else:
        recommendations.append('Make it at least 8 characters long')

    if len(pw) >= 12:
        score += 1

    if any(c.islower() for c in pw):
        score += 1
    else:
        recommendations.append('Add lowercase letters')

    if any(c.isupper() for c in pw):
        score += 1
    else:
        recommendations.append('Add uppercase letters')

    if any(c.isdigit() for c in pw):
        score += 1
    else:
        recommendations.append('Add digits')

    if any(not c.isalnum() for c in pw):
        score += 1
    else:
        recommendations.append('Add special characters (e.g. !@#$%)')

    lower = pw.lower()
    common = ['password', '1234', 'qwerty', 'admin', 'letmein', 'iloveyou']
    if any(c in lower for c in common):
        recommendations.append('Avoid common words or sequences')
        score = max(1, score - 2)

    normalized = max(0, min(4, int(score / 1.5)))
    return normalized, recommendations


@app.route('/')
def index():
    """Home page - list all recipes"""
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).paginate(page=page, per_page=6)
    return render_template('index.html', recipes=recipes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('register'))
        
        # Server-side password strength check
        pw_score, pw_recs = evaluate_password_server(password)
        # require at least a 'weak' score (2) to proceed
        if pw_score < 2:
            msg = 'Password is too weak. '
            if pw_recs:
                msg += 'Recommendations: ' + '; '.join(pw_recs[:3])
            flash(msg, 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with session handling and failed login tracking"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user is locked due to failed login attempts
        if user and user.is_locked():
            flash('Account temporarily locked. Please try again in 15 minutes.', 'warning')
            return redirect(url_for('login'))
        
        if user and user.check_password(password):
            user.reset_login_attempts()
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            # Security: validate next_page
            if next_page and not next_page.startswith('/'):
                next_page = None
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        
        # Record failed login attempt
        if user:
            user.record_failed_login()
            remaining = 3 - user.login_attempts
            if remaining > 0:
                flash(f'Invalid password. {remaining} attempts remaining.', 'danger')
            else:
                flash('Account locked due to too many failed login attempts. Please contact an admin.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    """Create new recipe"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        instructions = request.form.get('instructions', '').strip()
        cooking_time = request.form.get('cooking_time', type=int)
        servings = request.form.get('servings', type=int)
        difficulty = request.form.get('difficulty', 'Medium')
        
        # Validation
        if not all([title, description, ingredients, instructions]):
            flash('Title, description, ingredients, and instructions are required.', 'danger')
            return redirect(url_for('new_recipe'))
        
        if len(title) < 5:
            flash('Recipe title must be at least 5 characters.', 'danger')
            return redirect(url_for('new_recipe'))
        
        # Handle file upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            try:
                image_filename = secure_upload_file(file)
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('new_recipe'))
        
        # Create recipe
        recipe = Recipe(
            title=title,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            cooking_time=cooking_time,
            servings=servings,
            difficulty=difficulty,
            image_filename=image_filename,
            user_id=current_user.id
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        flash('Recipe created successfully!', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe.id))
    
    return render_template('new_recipe.html')

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    """View recipe details"""
    recipe = Recipe.query.get_or_404(recipe_id)
    comments = Comment.query.filter_by(recipe_id=recipe_id).order_by(Comment.created_at.desc()).all()
    return render_template('view_recipe.html', recipe=recipe, comments=comments)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    """Edit recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check authorization
    if recipe.user_id != current_user.id:
        flash('You do not have permission to edit this recipe.', 'danger')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    
    if request.method == 'POST':
        recipe.title = request.form.get('title', '').strip()
        recipe.description = request.form.get('description', '').strip()
        recipe.ingredients = request.form.get('ingredients', '').strip()
        recipe.instructions = request.form.get('instructions', '').strip()
        recipe.cooking_time = request.form.get('cooking_time', type=int)
        recipe.servings = request.form.get('servings', type=int)
        recipe.difficulty = request.form.get('difficulty', 'Medium')
        
        # Validation
        if not all([recipe.title, recipe.description, recipe.ingredients, recipe.instructions]):
            flash('All required fields must be filled.', 'danger')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))
        
        # Handle new image
        if 'image' in request.files:
            file = request.files['image']
            try:
                new_filename = secure_upload_file(file)
                # Delete old image if exists
                if recipe.image_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                recipe.image_filename = new_filename
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('edit_recipe', recipe_id=recipe_id))
        
        recipe.updated_at = datetime.now()
        db.session.commit()
        
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    """Delete recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check authorization
    if recipe.user_id != current_user.id:
        flash('You do not have permission to delete this recipe.', 'danger')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    
    # Delete image if exists
    if recipe.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(recipe)
    db.session.commit()
    
    flash('Recipe deleted successfully!', 'success')
    return redirect(url_for('my_recipes'))

@app.route('/my-recipes')
@login_required
def my_recipes():
    """View current user's recipes"""
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(
        Recipe.created_at.desc()
    ).paginate(page=page, per_page=6)
    return render_template('my_recipes.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    """Add comment to recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    
    if len(content) > 500:
        flash('Comment must be less than 500 characters.', 'danger')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    
    comment = Comment(content=content, user_id=current_user.id, recipe_id=recipe_id)
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully!', 'success')
    return redirect(url_for('view_recipe', recipe_id=recipe_id))

@app.route('/upload/<filename>')
def download_file(filename):
    """Download uploaded file"""
    # Security: prevent directory traversal
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Verify file exists and is within upload folder
    if not os.path.exists(filepath) or not os.path.abspath(filepath).startswith(
        os.path.abspath(app.config['UPLOAD_FOLDER'])
    ):
        flash('File not found.', 'danger')
        return redirect(url_for('index'))
    
    return send_file(filepath, as_attachment=True)

@app.route('/profile')
@login_required
def profile():
    """View user profile"""
    recipe_count = Recipe.query.filter_by(user_id=current_user.id).count()
    comment_count = Comment.query.filter_by(user_id=current_user.id).count()
    return render_template('profile.html', recipe_count=recipe_count, comment_count=comment_count)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow user to change their password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))
        
        # Validate new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))
        
        # Check password strength
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'danger')
            return redirect(url_for('change_password'))
        
        # Check against common passwords
        lower = new_password.lower()
        common = ['password', '1234', 'qwerty', 'admin', 'letmein', 'iloveyou']
        if any(c in lower for c in common):
            flash('New password is too common. Please choose a stronger password.', 'danger')
            return redirect(url_for('change_password'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('change_password'))
    
    return render_template('change_password.html')

@app.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Allow user to delete their own account"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_delete = request.form.get('confirm_delete', '')
        
        # Verify password
        if not current_user.check_password(password):
            flash('Password is incorrect.', 'danger')
            return redirect(url_for('delete_account'))
        
        # Verify confirmation
        if confirm_delete != 'DELETE':
            flash('Please type DELETE to confirm account deletion.', 'danger')
            return redirect(url_for('delete_account'))
        
        # Delete user's files
        for file in current_user.shared_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete user's recipe images
        for recipe in current_user.recipes:
            if recipe.image_filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
        
        # Delete user account (cascade will handle recipes, comments, etc.)
        user_id = current_user.id
        logout_user()
        db.session.delete(current_user)
        db.session.commit()
        
        flash('Your account has been deleted successfully.', 'info')
        return redirect(url_for('index'))
    
    return render_template('delete_account.html')

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@require_role(UserRole.ADMIN.value)
def admin_dashboard():
    """Admin dashboard for managing employees"""
    employees = User.query.filter_by(role=UserRole.EMPLOYEE.value).all()
    user_count = User.query.count()
    employee_count = User.query.filter_by(role=UserRole.EMPLOYEE.value).count()
    
    return render_template('admin_dashboard.html', 
                         employees=employees,
                         user_count=user_count,
                         employee_count=employee_count)

@app.route('/admin/create-employee', methods=['GET', 'POST'])
@require_role(UserRole.ADMIN.value)
def create_employee():
    """Create new employee account"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('create_employee'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return redirect(url_for('create_employee'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('create_employee'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('create_employee'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('create_employee'))
        
        # Server-side password strength check
        pw_score, pw_recs = evaluate_password_server(password)
        if pw_score < 2:
            msg = 'Password is too weak. '
            if pw_recs:
                msg += 'Recommendations: ' + '; '.join(pw_recs[:3])
            flash(msg, 'danger')
            return redirect(url_for('create_employee'))
        
        try:
            employee = User(username=username, email=email, role=UserRole.EMPLOYEE.value)
            employee.set_password(password)
            db.session.add(employee)
            db.session.commit()
            
            flash(f'Employee "{username}" created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('create_employee'))
    
    return render_template('create_employee.html')

@app.route('/admin/edit-employee/<int:employee_id>', methods=['GET', 'POST'])
@require_role(UserRole.ADMIN.value)
def edit_employee(employee_id):
    """Edit employee details"""
    employee = User.query.get_or_404(employee_id)
    
    # Ensure only employees can be edited
    if employee.role != UserRole.EMPLOYEE.value:
        flash('Can only edit employee accounts.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        
        # Validation
        if not all([new_username, new_email]):
            flash('Username and email are required.', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        if len(new_username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        # Check for duplicates (excluding current employee)
        if new_username != employee.username and User.query.filter_by(username=new_username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        if new_email != employee.email and User.query.filter_by(email=new_email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        employee.username = new_username
        employee.email = new_email
        db.session.commit()
        
        flash(f'Employee "{new_username}" updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_employee.html', employee=employee)

@app.route('/admin/reset-username/<int:employee_id>', methods=['POST'])
@require_role(UserRole.ADMIN.value)
def reset_username_permission(employee_id):
    """Grant employee permission to reset their username"""
    employee = User.query.get_or_404(employee_id)
    
    if employee.role != UserRole.EMPLOYEE.value:
        flash('Can only reset username permission for employees.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if employee.login_attempts >= 3:
        employee.username_reset_enabled = True
        employee.reset_login_attempts()
        db.session.commit()
        flash(f'Username reset enabled for {employee.username}. They can now reset their username.', 'success')
    else:
        flash(f'{employee.username} does not have 3 failed login attempts yet.', 'warning')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/view-shared-files')
@require_role(UserRole.ADMIN.value)
def admin_view_shared_files():
    """Admin can view all shared files (read-only, cannot download or modify)"""
    page = request.args.get('page', 1, type=int)
    shared_files = SharedFile.query.filter_by(is_active=True).order_by(
        SharedFile.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('admin_view_shared_files.html', shared_files=shared_files)

# ==================== EMPLOYEE ROUTES ====================

@app.route('/employee/dashboard')
@require_role(UserRole.EMPLOYEE.value)
def employee_dashboard():
    """Employee dashboard"""
    files_count = SharedFile.query.filter_by(user_id=current_user.id, is_active=True).count()
    return render_template('employee_dashboard.html', files_count=files_count)

@app.route('/employee/share-file', methods=['GET', 'POST'])
@require_role(UserRole.EMPLOYEE.value)
def share_file():
    """Employee can share PDF recipes"""
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('share_file'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('share_file'))
        
        try:
            filename = secure_upload_file(file, is_employee=True)
            file_size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            shared_file = SharedFile(
                filename=filename,
                original_filename=file.filename,
                description=description,
                file_size=file_size,
                user_id=current_user.id
            )
            
            db.session.add(shared_file)
            db.session.commit()
            
            flash('Recipe PDF shared successfully!', 'success')
            return redirect(url_for('employee_my_files'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('share_file'))
    
    return render_template('share_file.html')

@app.route('/employee/my-files')
@require_role(UserRole.EMPLOYEE.value)
def employee_my_files():
    """View employee's shared files"""
    page = request.args.get('page', 1, type=int)
    shared_files = SharedFile.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(SharedFile.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('employee_my_files.html', shared_files=shared_files)

@app.route('/employee/delete-file/<int:file_id>', methods=['POST'])
@require_role(UserRole.EMPLOYEE.value)
def delete_shared_file(file_id):
    """Delete shared file"""
    shared_file = SharedFile.query.get_or_404(file_id)
    
    # Verify ownership
    if shared_file.user_id != current_user.id:
        flash('You do not have permission to delete this file.', 'danger')
        return redirect(url_for('employee_my_files'))
    
    # Delete actual file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], shared_file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Mark as inactive instead of deleting (for audit trail)
    shared_file.is_active = False
    db.session.commit()
    
    flash('Recipe PDF deleted successfully!', 'success')
    return redirect(url_for('employee_my_files'))

@app.route('/employee/download-file/<int:file_id>')
@require_role(UserRole.EMPLOYEE.value)
def download_employee_file(file_id):
    """Download own shared file"""
    shared_file = SharedFile.query.get_or_404(file_id)
    
    # Verify ownership
    if shared_file.user_id != current_user.id:
        flash('You do not have permission to download this file.', 'danger')
        return redirect(url_for('employee_my_files'))
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], shared_file.filename)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('employee_my_files'))
    
    return send_file(file_path, as_attachment=True, download_name=shared_file.original_filename)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized!")
    app.run(debug=True, host='0.0.0.0', port=5000)
