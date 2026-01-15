import os
from dotenv import load_dotenv

load_dotenv()

Database_Url=os.getenv('DATABASE_URL')
origin=os.getenv('origin')