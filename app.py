from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Recipe, Comment
from config import config
import os
from datetime import datetime
from functools import wraps
import secrets

app = Flask(__name__)
app.config.from_object(config['development'])

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

def secure_upload_file(file):
    """Sanitize and secure file upload"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(app.config['ALLOWED_EXTENSIONS'])}")
    
    # Generate random filename to prevent directory traversal
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secrets.token_hex(16) + '.' + ext
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return filename


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
    """User login with session handling"""
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
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            # Security: validate next_page
            if next_page and not next_page.startswith('/'):
                next_page = None
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        
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
        
        recipe.updated_at = datetime.utcnow()
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
