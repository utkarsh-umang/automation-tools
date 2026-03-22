# Add your SQLModel table models here. Import them in this __init__.py
# so Alembic discovers them.
from app.models.user import User, UserRole  # noqa: F401
