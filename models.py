from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta
from enum import Enum

# Initialize Argon2 password hasher
pw_hasher = PasswordHasher()

db = SQLAlchemy()

class UserRole(Enum):
    """User roles in the system"""
    USER = "user"  # Regular user - can create recipes
    EMPLOYEE = "employee"  # Restaurant employee - can share PDF recipes
    ADMIN = "admin"  # Admin - manages employees

class User(UserMixin, db.Model):
    """User model with authentication and roles"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default=UserRole.USER.value, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    login_attempts = db.Column(db.Integer, default=0)  # Failed login attempts
    last_login_attempt = db.Column(db.DateTime)  # Last failed login time
    username_reset_enabled = db.Column(db.Boolean, default=False)  # Admin can reset username
    
    # Relationships
    recipes = db.relationship('Recipe', backref='author', lazy=True, cascade='all, delete-orphan')
    shared_files = db.relationship('SharedFile', backref='uploader', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password with Argon2"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = pw_hasher.hash(password)
    
    def check_password(self, password):
        """Check password against Argon2 hash"""
        try:
            pw_hasher.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        self.login_attempts += 1
        self.last_login_attempt = datetime.now()
        db.session.commit()
    
    def reset_login_attempts(self):
        """Reset login attempts after successful login"""
        self.login_attempts = 0
        self.last_login_attempt = None
        db.session.commit()
    
    def is_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.login_attempts >= 3:
            # Lock for 15 minutes
            if self.last_login_attempt:
                lockout_time = self.last_login_attempt + timedelta(minutes=15)
                if datetime.now() < lockout_time:
                    return True
            # If lockout period passed, reset attempts
            self.reset_login_attempts()
        return False
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Recipe(db.Model):
    """Recipe model for food recipes"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)  # JSON format or comma-separated
    instructions = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer)  # in minutes
    servings = db.Column(db.Integer)
    difficulty = db.Column(db.String(50), default='Medium')  # Easy, Medium, Hard
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='recipe', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Recipe {self.title}>'

class Comment(db.Model):
    """Comment model for recipe feedback"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    
    def __repr__(self):
        return f'<Comment by {self.user.username}>'

class SharedFile(db.Model):
    """Model for files shared by employees"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_size = db.Column(db.Integer)  # in bytes
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<SharedFile {self.original_filename} by {self.uploader.username}>'
