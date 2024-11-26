import mysql.connector
from sqlalchemy import create_engine
import pandas as pd



class Database:
    def __init__(self): 
        # Define connection parameters
        self.user = 'root'
        self.password = '********'
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


    def load_table(self, table_name: str) -> pd.DataFrame:
            try:
                # Load table from MySQL to a DataFrame
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(query, con=self.engine)
                print(f"Table `{table_name}` loaded successfully!")
                return df
            except Exception as e:
                print(f"An error occurred: {e}")
                return None



