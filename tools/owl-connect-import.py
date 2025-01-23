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

# Create file handler which logs even debug messages
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

def setup_logger():
    """Configure and return a logger with file and console output"""
    return logger

def sanitize_column_name(name):
    """Sanitize column names for SQL compatibility"""
    # Remove special characters and replace with underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name)).lower()
    
    # Ensure the name doesn't start with a number
    if name[0].isdigit():
        name = f'col_{name}'
    
    logger.debug(f"Sanitized column name: {name}")
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

Base = declarative_base()

class CDCChangeLog(Base):
    """Model to track changes during data import"""
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

def perform_cdc(df, engine, table_name='owl_connect_export'):
    """
    Perform Change Data Capture by comparing new data with existing data
    
    Args:
        df (pd.DataFrame): New dataframe to import
        engine (sqlalchemy.engine.base.Engine): Database engine
        table_name (str): Name of the target table
    
    Returns:
        pd.DataFrame: DataFrame with change tracking information
    """
    # Create a session
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    
    # Create CDC change log table if not exists
    Base.metadata.create_all(engine)
    
    try:
        # Check for case-insensitive and hyphen/underscore flexible table name match
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        logger.debug(f"All tables in database: {all_tables}")
        
        matching_tables = [
            t for t in all_tables 
            if (t.lower() == table_name.lower() or 
                t.lower().replace('-', '_') == table_name.lower().replace('-', '_'))
        ]
        
        if not matching_tables:
            logger.warning(f"No table found matching '{table_name}'. Performing first-time import.")
            
            # Provide more detailed logging about potential matches
            similar_tables = [
                t for t in all_tables 
                if table_name.lower() in t.lower() or t.lower() in table_name.lower()
            ]
            if similar_tables:
                logger.info(f"Similar tables found: {similar_tables}")
            
            # First-time import logic remains the same
            inserts_count = len(df)
            for _, new_row in df.iterrows():
                new_row_hash = compute_record_hash(new_row)
                
                change_log = CDCChangeLog(
                    change_type='INSERT',
                    table_name=table_name,
                    record_id=new_row_hash,
                    new_data=str(new_row.to_dict())
                )
                session.add(change_log)
            
            session.commit()
            logger.info(f"First-time import: {inserts_count} records inserted")
            
            return df
        
        # Use the exact table name from matching tables
        exact_table_name = matching_tables[0]
        logger.debug(f"Found matching table: {exact_table_name}")
        
        # Read existing data from the table
        existing_df = pd.read_sql_table(exact_table_name, engine)
        logger.info(f"Total existing records: {exact_table_name}: {len(existing_df)}")
        
        # Add hash columns to both dataframes for tracking
        df['record_hash'] = df.apply(compute_record_hash, axis=1)
        existing_df['record_hash'] = existing_df.apply(compute_record_hash, axis=1)
        
        # Log hash generation details for debugging
        logger.debug(f"New DataFrame first hash: {df['record_hash'].iloc[0]} - {df.head(1).to_json()}")
        logger.debug(f"Existing DataFrame first hash: {existing_df['record_hash'].iloc[0]} - {existing_df.head(1).to_json()}")
        
        # Track changes
        inserts_count = 0
        updates_count = 0
        deletes_count = 0
        no_changes_count = 0  # Track rows with no changes
        
        # Detect and handle updates and inserts
        for _, new_row in df.iterrows():
            # Early check: Find matching rows in existing data by hash
            matching_rows = existing_df[existing_df['record_hash'] == new_row['record_hash']]
            
            # If hash matches, it's potentially an unchanged record
            if len(matching_rows) > 0:
                # Early exit if hash is identical
                no_changes_count += 1
                logger.debug(f"NO CHANGE: Record with hash {new_row['record_hash']} remains unchanged")
                continue
            
            # If no matching hash, treat as a new record
            change_log = CDCChangeLog(
                change_type='INSERT',
                table_name=exact_table_name,
                record_id=new_row['record_hash'],
                new_data=str(new_row.drop('record_hash'))
            )
            session.add(change_log)
            inserts_count += 1
            
            logger.debug(f"INSERT: New record with hash {new_row['record_hash']} added")
        
        # Additional pass to detect updates in existing records
        for _, existing_row in existing_df.iterrows():
            # Skip if the record's hash is in the new dataset
            if existing_row['record_hash'] in df['record_hash'].values:
                continue
            
            # This is a record to be deleted
            change_log = CDCChangeLog(
                change_type='DELETE',
                table_name=exact_table_name,
                record_id=existing_row['record_hash'],
                old_data=str(existing_row.drop('record_hash'))
            )
            session.add(change_log)
            deletes_count += 1
            
            logger.debug(f"DELETE: Record with hash {existing_row['record_hash']} will be removed from {exact_table_name}")
        
        # Log summary of changes
        logger.info(f"Change Summary for {exact_table_name}:")
        logger.info(f"  Inserts: {inserts_count}")
        logger.info(f"  Updates: {updates_count}")
        logger.info(f"  Unchanged: {no_changes_count}")
        logger.info(f"  Deletes: {deletes_count}")
        logger.info(f"  Total Processed: {len(df)}")
        
        # Commit changes to change log
        session.commit()
        
        # Info level logging for summary
        logger.info(f"CDC Summary: {inserts_count} inserts, {updates_count} updates, {deletes_count} deletes")
        
        # Remove hash column before final import
        final_df = df.drop(columns=['record_hash'])
        
        return final_df
    
    except Exception as e:
        session.rollback()
        logger.error(f"CDC Error: {e}")
        raise
    finally:
        session.close()

def import_excel_to_mysql(excel_path, sheet_name, engine):
    """Updated import function with CDC"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Rename columns to be SQL-friendly
        df.columns = [sanitize_column_name(col) for col in df.columns]
        
        # Perform Change Data Capture
        df = perform_cdc(df, engine)
        
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
        df = import_excel_to_mysql(excel_path, sheet_name, engine)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main()