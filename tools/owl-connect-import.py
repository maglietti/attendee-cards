import pandas as pd
import os
import re
import logging
from logging.handlers import RotatingFileHandler
import sqlalchemy
from sqlalchemy import create_engine
from dotenv import load_dotenv
import hashlib
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, inspect
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# Create a global logger
logger = logging.getLogger('owl_connect_import')
logger.setLevel(logging.INFO)

# Create console handler and set level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler and set level to DEBUG
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'owl_connect_import.log'),
    maxBytes=1048576,  # 1MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Create formatters
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatters to handlers
console_handler.setFormatter(console_formatter)
file_handler.setFormatter(file_formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def sanitize_column_name(name):
    """
    Sanitize column names to ensure SQL compatibility.

    Transforms input column names by removing special characters, 
    converting to lowercase, and ensuring they start with a valid character.

    Args:
        name (str): The original column name to be sanitized.

    Returns:
        str: A SQL-friendly column name with only alphanumeric characters and underscores.

    Notes:
        - Special characters are replaced with underscores
        - Names are converted to lowercase
        - Names starting with a digit are prefixed with 'col_'
    """
    # Remove special characters and replace with underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name)).lower()
    
    # Ensure the name doesn't start with a number
    if name[0].isdigit():
        name = f'col_{name}'
    
    logger.debug(f"Sanitized column name: {name}")
    return name

def load_database_config():
    """
    Load database configuration from a .env file.

    Reads database connection parameters from an environment file located 
    in the parent directory. Validates the presence of critical configuration.

    Returns:
        dict: A dictionary containing database connection parameters with keys:
            - 'host': Database host (defaults to 'localhost')
            - 'user': Database username
            - 'password': Database password
            - 'database': Database name (defaults to 'attendees_db')

    Raises:
        ValueError: If required configuration parameters are missing.

    Notes:
        - Uses python-dotenv to load environment variables
        - Looks for .env file in the parent directory of the script
        - Provides default values for some configuration parameters
    """
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
    """
    Create a SQLAlchemy database connection engine.

    Generates a database connection engine using the provided configuration,
    specifically for MySQL databases with the mysqlconnector dialect.

    Args:
        db_config (dict): Database configuration dictionary containing 
                          'user', 'password', 'host', and 'database' keys.

    Returns:
        sqlalchemy.engine.base.Engine: A configured database connection engine.

    Notes:
        - Uses MySQL connector for database connections
        - Constructs a connection string from the provided configuration
        - Suitable for use with pandas and SQLAlchemy ORM operations
    """
    connection_string = (
        f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}/{db_config['database']}"
    )
    return create_engine(connection_string)

# Base class for SQLAlchemy ORM models, enabling declarative table definitions
Base = declarative_base()

class CDCChangeLog(Base):
    """
    SQLAlchemy ORM model for tracking data changes during import operations.

    This model maintains a comprehensive log of changes made during data import,
    providing a detailed audit trail for each modification to the database.

    Attributes:
        id (int): Unique identifier for each change log entry, auto-incremented.
        change_type (str): Type of change ('INSERT', 'UPDATE', 'DELETE').
        table_name (str): Name of the table where the change occurred.
        record_id (str): Identifier of the specific record that was modified.
        old_data (str, optional): Previous state of the record before modification.
        new_data (str, optional): Updated state of the record after modification.
        changed_at (datetime): Timestamp of when the change was recorded.

    Note:
        This model is crucial for maintaining data integrity and tracking 
        historical changes in the database during import processes.
    """
    __tablename__ = 'owl_connect_change_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    change_type = Column(String(20), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    table_name = Column(String(100), nullable=False)
    record_id = Column(String(255), nullable=False)
    old_data = Column(Text, nullable=True)
    new_data = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)  

def compute_record_hash(row, exclude_columns=None):
    """
    Generate a unique, consistent hash for a record to track changes
    
    Args:
        row (pd.Series): A single row of data
        exclude_columns (list, optional): Columns to exclude from hash generation
    
    Returns:
        str: A consistent MD5 hash for the row
    """
    # Default list of columns to exclude
    if exclude_columns is None:
        exclude_columns = [
            'created_at', 'updated_at', 'timestamp', 
            'record_hash', 'registrant_date'
        ]
    
    # Create a filtered dictionary of the row, excluding specified columns
    filtered_row = {}
    for k, v in row.items():
        if k not in exclude_columns:
            # Consistent handling of various "empty" values
            if pd.isna(v) or v is None:
                # Normalize all "empty" values to a consistent string
                filtered_row[k] = 'null'
            elif isinstance(v, (int, float)):
                # Truncate long numbers to first 10 digits
                filtered_row[k] = str(int(v))[:10] if len(str(v)) > 10 else str(v)
            elif isinstance(v, str):
                # Strip whitespace, convert to lowercase
                filtered_row[k] = v.strip().lower()
            else:
                # Convert all other types to lowercase string
                filtered_row[k] = str(v).strip().lower()
    
    # Sort the dictionary to ensure consistent ordering
    sorted_items = sorted(filtered_row.items())
    
    # Create a consistent string representation
    row_str = '|'.join(f"{k}:{v}" for k, v in sorted_items)
    
    # Create the hash for this row
    hash_value = hashlib.md5(row_str.encode('utf-8')).hexdigest()
    
    # Log detailed hash generation information
    logger.debug(f"Hash Generation Details:")
    logger.debug(f"  Raw Row Data: {dict(row)}")
    logger.debug(f"  Filtered Row Data: {filtered_row}")
    logger.debug(f"  Row String: {row_str}")
    logger.debug(f"  Generated Hash: {hash_value}")
    
    return hash_value

def ensure_table_exists(df: pd.DataFrame, engine: sqlalchemy.engine.base.Engine, table_name: str, session: sqlalchemy.orm.Session) -> dict:
    """
    Ensure the specified table exists, creating it if necessary.
    
    Args:
        df (pd.DataFrame): DataFrame to be imported
        engine (sqlalchemy.engine.base.Engine): Database connection engine
        table_name (str): Name of the target table
        session (sqlalchemy.orm.Session): Active database session
    
    Returns:
        dict: A dictionary containing import details and the exact table name
    """
    # Check for case-insensitive and hyphen/underscore flexible table name match
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    logger.debug(f"All tables in database: {all_tables}")
    
    matching_tables = [
        t for t in all_tables 
        if (t.lower() == table_name.lower() or 
            t.lower().replace('-', '_') == table_name.lower().replace('-', '_'))
    ]
    
    # Use the exact table name from matching tables
    exact_table_name = matching_tables[0]
    logger.debug(f"Found matching table: {exact_table_name}")
    
    # First-time import or table doesn't exist
    if not matching_tables:
        logger.warning(f"No table found matching '{table_name}'. Performing first-time import.")
        
        # Add hash column for tracking
        df['record_hash'] = df.apply(compute_record_hash, axis=1)
        
        # Prepare first-time import changes
        changes = {
            'inserts': len(df),
            'updates': 0,
            'deletes': 0,
            'unchanged': 0,
            'total_processed': len(df),
            'table_name': None
        }
        
        # Log each record being inserted
        for _, new_row in df.iterrows():
            change_log = CDCChangeLog(
                change_type='INSERT',
                table_name=table_name,
                record_id=new_row['record_hash'],
                new_data=str(new_row.drop('record_hash'))
            )
            session.add(change_log)
            logger.debug(f"INSERT: New record with hash {new_row['record_hash']} added")
        
        # Save the entire dataframe to the database
        normalized_table_name = table_name.lower().replace('-', '_')
        df.to_sql(normalized_table_name, engine, if_exists='replace', index=False)
        
        # Commit changes to change log
        session.commit()
        
        # Update table name in changes
        changes['table_name'] = normalized_table_name
        
        logger.info(f"First-time import: {changes['inserts']} records inserted")
        return changes
    
    # Return a dictionary with the table name for consistency
    return {
        'table_name': exact_table_name,
        'inserts': 0,
        'updates': 0,
        'deletes': 0,
        'unchanged': 0,
        'total_processed': 0
    }

def perform_cdc(df: pd.DataFrame, engine: sqlalchemy.engine.base.Engine, table_name: str = 'owl_connect_export') -> dict:
    """
    Perform Change Data Capture (CDC) on a given DataFrame.
    
    Identifies and logs changes between the input DataFrame and existing database records.
    
    Args:
        df (pd.DataFrame): New data to be compared with existing records
        engine (sqlalchemy.engine.base.Engine): Database connection engine
        table_name (str, optional): Name of the target table. Defaults to 'owl_connect_export'.
    
    Returns:
        dict: Summary of changes detected during the import process
    """
    # Create a session
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    
    # Create CDC change log table if not exists
    Base.metadata.create_all(engine)
    
    try:
        # Validate input
        if df.empty:
            logger.warning(f"Empty DataFrame provided for table {table_name}. No changes processed.")
            return {
                'inserts': 0,
                'updates': 0,
                'deletes': 0,
                'unchanged': 0,
                'total_processed': 0
            }
        
        # Ensure table exists or create it
        table_info = ensure_table_exists(df, engine, table_name, session)
        
        # If this was a first-time import, return the changes
        if table_info.get('inserts', 0) > 0:
            return table_info
        
        # Read existing data from the table
        exact_table_name = table_info['table_name']
        existing_df = pd.read_sql_table(exact_table_name, engine)
        logger.info(f"Total existing records: {exact_table_name}: {len(existing_df)}")
        
        # Add hash columns to both dataframes for tracking
        df['record_hash'] = df.apply(compute_record_hash, axis=1)
        existing_df['record_hash'] = existing_df.apply(compute_record_hash, axis=1)
        
        # Initialize change tracking
        changes = {
            'inserts': 0,
            'updates': 0,
            'deletes': 0,
            'unchanged': 0,
            'total_processed': len(df)
        }
        
        # Identify new records (inserts)
        new_records = df[~df['record_hash'].isin(existing_df['record_hash'])]
        for _, new_row in new_records.iterrows():
            change_log = CDCChangeLog(
                change_type='INSERT',
                table_name=exact_table_name,
                record_id=new_row['record_hash'],
                new_data=str(new_row.drop('record_hash'))
            )
            session.add(change_log)
            changes['inserts'] += 1
            logger.debug(f"INSERT: New record with hash {new_row['record_hash']} added")
        
        # Identify records to be deleted
        deleted_records = existing_df[~existing_df['record_hash'].isin(df['record_hash'])]
        for _, deleted_row in deleted_records.iterrows():
            change_log = CDCChangeLog(
                change_type='DELETE',
                table_name=exact_table_name,
                record_id=deleted_row['record_hash'],
                old_data=str(deleted_row.drop('record_hash'))
            )
            session.add(change_log)
            changes['deletes'] += 1
            logger.debug(f"DELETE: Record with hash {deleted_row['record_hash']} will be removed from {exact_table_name}")
        
        # Identify unchanged records
        changes['unchanged'] = len(df[df['record_hash'].isin(existing_df['record_hash'])])
        
        # Log summary of changes
        logger.info(f"Change Summary for {exact_table_name}:")
        for change_type, count in changes.items():
            logger.info(f"  {change_type.capitalize()}: {count}")
        
        # Commit changes to change log
        session.commit()
        
        return changes
    
    except Exception as e:
        session.rollback()
        logger.error(f"CDC Error: {e}")
        raise
    finally:
        session.close()

def import_excel_to_mysql(excel_path, sheet_name, engine):
    """
    Import an Excel file to a MySQL database with Change Data Capture (CDC) functionality.

    This function reads an Excel file, sanitizes column names, performs change tracking,
    and imports the data into a MySQL database table named 'owl_connect_export'.

    Args:
        excel_path (str): Full path to the Excel file to be imported.
        sheet_name (str): Name of the sheet in the Excel file to import.
        engine (sqlalchemy.engine.base.Engine): SQLAlchemy database connection engine.

    Returns:
        pandas.DataFrame: The imported DataFrame with sanitized column names.

    Raises:
        FileNotFoundError: If the specified Excel file does not exist.
        ValueError: If the sheet_name is invalid or does not exist in the Excel file.
        sqlalchemy.exc.SQLAlchemyError: For database connection or import errors.
        Exception: For any other unexpected errors during the import process.

    Notes:
        - Column names are automatically sanitized to be SQL-friendly.
        - Uses Change Data Capture (CDC) to track and log data changes.
        - Existing data in the 'owl_connect_export' table will be replaced.
        - Logs import progress and any errors encountered.
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Rename columns to be SQL-friendly
        df.columns = [sanitize_column_name(col) for col in df.columns]
        
        # Perform Change Data Capture
        changes = perform_cdc(df, engine)
        
        # Import to MySQL
        logger.info(f"Importing data from {excel_path}")
        df.to_sql('owl_connect_export', engine, if_exists='replace', index=False)
        
        logger.info(f"Successfully imported {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error importing Excel file: {e}")
        raise

def main():
    """
    Main script entry point for importing Owl Connect event details into a MySQL database.

    This function orchestrates the entire Excel file import process, including:
    1. Loading database configuration from a .env file
    2. Creating a SQLAlchemy database connection engine
    3. Importing an Excel file containing event details
    4. Performing Change Data Capture (CDC) to track data modifications
    5. Logging the import process and handling potential errors

    The script is designed to:
    - Read an Excel file with event details from a predefined path
    - Sanitize column names for SQL compatibility
    - Import data into a MySQL database table
    - Track and log any changes made during the import process

    Raises:
        Exception: If any errors occur during database configuration, 
                   file import, or database operations.

    Notes:
        - Requires a .env file in the parent directory for database configuration
        - Uses a hardcoded Excel file path and sheet name
        - Logs import progress and errors to a rotating log file
    """
    try:
        # Excel file configuration
        excel_path = '/Users/maglietti/Code/magliettiGit/attendee-cards/owl-connect/Event_Detail_Report.xlsx'
        sheet_name = 'Event Detail'
        
        # Load database configuration
        db_config = load_database_config()
        
        # Create database engine
        engine = create_sqlalchemy_engine(db_config)
        
        # Import Excel to MySQL
        df = import_excel_to_mysql(excel_path, sheet_name, engine)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main()