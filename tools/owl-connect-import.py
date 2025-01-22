import pandas as pd
import os
import re
import logging
from logging.handlers import RotatingFileHandler
import sqlalchemy
from sqlalchemy import create_engine
from dotenv import load_dotenv

def setup_logger():
    """Configure and return a logger with file and console output"""
    # Create a logger
    logger = logging.getLogger('owl_connect_import')
    logger.setLevel(logging.INFO)

    # Create console handler and set level to INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create file handler which logs even debug messages
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'owl_connect_import.log'),
        maxBytes=1048576,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Create formatters
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatters to handlers
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def sanitize_column_name(name, logger):
    """Sanitize column names"""
    # Convert to lowercase
    name = name.lower()
    # Replace any non-alphanumeric characters with underscores
    name = re.sub(r'[^a-z0-9]+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Ensure it doesn't start with a number
    if name[0].isdigit():
        name = f'col_{name}'
    
    logger.info(f"Sanitized column name: {name}")
    return name

def load_database_config():
    """Load database configuration from .env file"""
    # Use the parent directory's .env file
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=env_path)
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME', 'attendees_db')
    }
    
    # Validate required configuration
    required_keys = ['user', 'password']
    for key in required_keys:
        if not db_config[key]:
            raise ValueError(f"Missing required database configuration: {key}")
    
    return db_config

def create_sqlalchemy_engine(db_config):
    """Create SQLAlchemy engine for database connection"""
    connection_string = (
        f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}/{db_config['database']}"
    )
    return create_engine(connection_string)

def import_excel_to_mysql(excel_path, sheet_name, engine, logger):
    """Import Excel data to MySQL"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Rename columns to be SQL-friendly
        df.columns = [sanitize_column_name(col, logger) for col in df.columns]
        
        # Import to MySQL
        logger.info(f"Importing data from {excel_path}")
        df.to_sql('owl-connect-export', engine, if_exists='replace', index=False)
        
        logger.info(f"Successfully imported {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error importing Excel file: {e}")
        raise

def main():
    # Setup logger
    logger = setup_logger()
    
    try:
        # Excel file configuration
        excel_path = '/Users/maglietti/Code/magliettiGit/attendee-cards/owl-connect/Event_Detail_Report.xlsx'
        sheet_name = 'Event Detail'
        
        # Load database configuration
        db_config = load_database_config()
        
        # Create database engine
        engine = create_sqlalchemy_engine(db_config)
        
        # Import Excel to MySQL
        df = import_excel_to_mysql(excel_path, sheet_name, engine, logger)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main()