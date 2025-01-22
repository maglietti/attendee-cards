import pandas as pd
import os
import re
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Configure and return a logger with file and console output"""
    # Create a logger
    logger = logging.getLogger('owl_connect_table')
    logger.setLevel(logging.INFO)

    # Create console handler and set level to INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create file handler which logs even debug messages
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'owl_connect_table.log'),
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

def analyze_excel_file(file_path, sheet, logger):
    """Analyze the Excel file and log column information"""
    logger.info(f"Reading Excel file: {file_path}")
    logger.info(f"Sheet: {sheet}")
    
    # Read the Excel file
    try:
        df = pd.read_excel(file_path, sheet_name=sheet)
        
        # Log column details
        logger.debug("Excel File Column Analysis:")
        for column in df.columns:
            logger.debug(f"Column: {column}")
            logger.debug(f"Data Type: {df[column].dtype}")
            logger.debug(f"Sample Value: {df[column].head(1).tolist()}")
        
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        raise

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

def generate_create_table_sql(df, logger):
    """Generate SQL to create table based on Excel file structure"""
    logger.info("Generating CREATE TABLE SQL")
    
    # Start building the CREATE TABLE SQL
    columns = []
    for column in df.columns:   
        safe_column = sanitize_column_name(column, logger)
        
        # Map pandas dtypes to MySQL column types
        if df[column].dtype == 'object':
            # For string columns, use VARCHAR with a reasonable max length
            max_length = df[column].astype(str).str.len().max()
            col_type = f'VARCHAR({min(max(max_length, 50), 255)})'
        elif df[column].dtype == 'int64':
            col_type = 'INT'
        elif df[column].dtype == 'float64':
            col_type = 'DECIMAL(10,2)'
        elif 'datetime' in str(df[column].dtype):
            col_type = 'DATETIME'
        else:
            col_type = 'TEXT'
        
        columns.append(f"{safe_column} {col_type}")
    
    # Create full SQL statement
    create_table_sql = f"""
-- Create owl-connect-export table
CREATE TABLE IF NOT EXISTS `owl-connect-export` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    {',\n    '.join(columns)}
);
"""
    logger.debug(create_table_sql)
    logger.info("CREATE TABLE SQL generated successfully")
    return create_table_sql

def write_sql_to_file(sql, output_path, logger):
    """Write SQL to a file"""
    try:
        with open(output_path, 'w') as f:
            f.write(sql)
        logger.info(f"SQL written to {output_path}")
    except Exception as e:
        logger.error(f"Error writing SQL to file: {e}")
        raise

def main():
    # Setup logger
    logger = setup_logger()
    
    try:
        # Specific path to the Excel file
        excel_path = '/Users/maglietti/Code/magliettiGit/attendee-cards/owl-connect/Event_Detail_Report.xlsx'
        workbook_sheet = 'Event Detail'
        
        # Output SQL file path
        output_sql_path = os.path.join(os.path.dirname(__file__), 'owl-connect-table.sql')
        
        # Analyze the Excel file
        df = analyze_excel_file(excel_path, workbook_sheet, logger)
        
        # Generate CREATE TABLE SQL
        create_table_sql = generate_create_table_sql(df, logger)
        
        # Write SQL to file
        write_sql_to_file(create_table_sql, output_sql_path, logger)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main()