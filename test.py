import pandas as pd
from sqlalchemy import create_engine

class Database:
    def __init__(self): 
        # Define connection parameters
        self.user = 'root'
        self.password = '*********'
        self.host = 'localhost'
        self.database = 'bourse'

        # Create the database connection URL
        self.connection_string = f'mysql+mysqlconnector://{self.user}:{self.password}@{self.host}/{self.database}'

        # Create SQLAlchemy engine
        self.engine = create_engine(self.connection_string)

    def save_dataframe(self, df: pd.DataFrame, table_name: str):
        try:
            # Save DataFrame to MySQL table
            df.to_sql(table_name, con=self.engine, if_exists='replace', index=False)
            print(f"DataFrame successfully saved to table `{table_name}`")
        except Exception as e:
            print(f"An error occurred: {e}")

# Example usage:

# Create an instance of the Database class
db = Database()

# Example DataFrame
data = {
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
}

df = pd.DataFrame(data)

# Save the DataFrame to MySQL
db.save_dataframe(df, 'your_table_name')
