import os
from dotenv import load_dotenv
from app.database import Base  # Path to your Base/models
import app.models             # Ensures all model tables are registered

load_dotenv()

# Overwrite sqlalchemy.url with your environment variable
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Set the target metadata for autogenerate
target_metadata = Base.metadata