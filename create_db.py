from database import engine, Base
from modules import User  # Ensure this is imported so SQLAlchemy sees the model

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully.")
