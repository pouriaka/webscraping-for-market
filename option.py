from tsetmc import *
import threading
import pandas as pd
import jdatetime
from datetime import datetime



class option:
    def __init__(self):
        self.intrest_rate = 30


    @staticmethod
    def find_underlying_asset(symbol_name):
        # Use regex to remove digits, hyphens, and the word related to call or put option
        cleaned_string = re.sub(r'\d+|-|اختيارخ|/|اختيارف', '', symbol_name, flags=re.IGNORECASE)
        # Return the cleaned string, also stripping any extra spaces that may result
        return cleaned_string.strip()
    

    @staticmethod
    def find_strike_price(symbol_name):
        # Find the position of the first dash
        first_dash = symbol_name.find('-')
        
        # Find the position of the second dash
        second_dash = symbol_name.find('-', first_dash + 1)
        
        # Extract the substring between the first and second dash
        if first_dash != -1 and second_dash != -1:
            return float(symbol_name[first_dash + 1:second_dash])
        else:
            return "Can't find strike price."


    # Function to parse the date from the string
    @staticmethod
    def extract_persian_date(s):
        # Split the string by '-' to extract the components
        parts = s.split('-')
        
        if len(parts) != 3:
            raise ValueError("Invalid format")
        
        date_str = parts[2].strip()

        # Check if the date is in the Gregorian format (YY/MM/DD) or Persian format (YYYYMMDD)
        if '/' in date_str:
            # For dates in Gregorian style like "03/07/29", we assume the first number is the year in Persian
            year = int(date_str.split('/')[0]) + 1400  # Adding 1400 to convert to Persian year
            month = date_str.split('/')[1]
            day = date_str.split('/')[2]
            persian_date = f"{year}/{month}/{day}"
        else:
            # If the date is already in Persian format like "14030827"
            if len(date_str) == 8:  # Check for Persian date without '/'
                persian_date = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
            else:
                raise ValueError("Invalid date format")

        return persian_date
    

    def find_days_to_strike(self, symbol_name):
        strick_date = self.extract_persian_date(symbol_name)

        # Convert the input string to a jdatetime (Jalali datetime) object
        year, month, day = map(int, strick_date.split('/'))
        target_date_jalali = jdatetime.date(year, month, day)
        
        # Convert the target Jalali date to Gregorian date
        target_date_gregorian = target_date_jalali.togregorian()
        
        # Get today's Gregorian date
        today_gregorian = datetime.today().date()
        
        # Calculate the difference in days
        days_difference = (target_date_gregorian - today_gregorian).days
        
        return days_difference
        
        
    def coverdcall_calculate(self, underlying_asset_price, premium, strike, day_to_strike, intrest_rate, tax_and_fee=True):
        if tax_and_fee:
            stock_buy_fee_and_tax = underlying_asset_price * 0.003712
            option_sell_fee = premium * 0.00103
            strike_fee = strike * 0.0005
            strike_tax = strike * 0.005

            # Because we pay the strike fee and tax at the end of the option, we reback the intrest of this money
            strike_fee_and_tax_reback = (strike_fee + strike_tax) * (day_to_strike/365) * (intrest_rate/100) 

            take_coverdcall_fee_and_tax = stock_buy_fee_and_tax + option_sell_fee 
            all_fee_and_tax = stock_buy_fee_and_tax + option_sell_fee + strike_fee + strike_tax

            capital_involved = (underlying_asset_price + take_coverdcall_fee_and_tax) - premium
            profit = (strike + premium) - (underlying_asset_price + all_fee_and_tax) + strike_fee_and_tax_reback
            profit_percent = (profit / capital_involved) * 100
            profit_per_year= (profit_percent * 365) / day_to_strike
            profit_per_month = profit_per_year / 12
            otm_point = strike
            otm_percent = ((underlying_asset_price - otm_point)/underlying_asset_price) * 100
            loss_point = underlying_asset_price - premium
            loss_percent = ((underlying_asset_price - loss_point)/underlying_asset_price) * 100

            profit_per_year = round(profit_per_year, 2)
            profit_per_month = round(profit_per_month, 2)
            otm_percent = round(otm_percent, 2)
            loss_percent = round(loss_percent, 2)

            return profit_per_year, profit_per_month, otm_percent, loss_percent

        else:
            capital_involved = underlying_asset_price - premium
            profit = (strike + premium) - underlying_asset_price 
            profit_percent = (profit / capital_involved) * 100
            profit_per_year= (profit_percent * 365) / day_to_strike
            profit_per_month = profit_per_year / 12
            otm_point = strike
            otm_percent = ((underlying_asset_price - otm_point)/underlying_asset_price) * 100
            loss_point = underlying_asset_price - premium
            loss_percent = ((underlying_asset_price - loss_point)/underlying_asset_price) * 100

            profit_per_year = round(profit_per_year, 2)
            profit_per_month = round(profit_per_month, 2)
            otm_percent = round(otm_percent, 2)
            loss_percent = round(loss_percent, 2)

            return profit_per_year, profit_per_month, otm_percent, loss_percent


    def coverdcall_filter(self, tax_and_fee=False):       
        # Create a pandas DataFrame to save filterd data
        coverdcall_filter_df = pd.DataFrame()
        update_coverdcall_filter_df = pd.DataFrame()

        while True:
            # Load a table from MySQL into a DataFrame
            self.df = Database().load_table('tsetmc_data')
            self.option_df = Database().load_table('option_data')
            self.underlying_asset_df = Database().load_table('underlying_assets')

            for i in range(len(self.option_df)):
                option_symbol = self.find_underlying_asset(self.option_df.iloc[i]['نام'])
                # Find underlying asset price from all symbol df
                for j in range(len(self.underlying_asset_df)):
                    if option_symbol == self.underlying_asset_df.iloc[j]['نماد']:
                        option_underlying_asset_price = float(self.underlying_asset_df.iloc[j]['قیمت فروش'])
                        
                option_strike = self.find_strike_price(self.option_df.iloc[i]['نام'])
                option_premium = float(self.option_df.iloc[i]['قیمت خرید'])
                option_days_to_strike = self.find_days_to_strike(self.option_df.iloc[i]['نام'])

                # If option is ITM we calculate coverd call for it
                if option_underlying_asset_price > option_strike and "اختيارخ" in self.option_df.iloc[i]['نام']:
                    # Calculate coverd call data
                    year_p, month_p, otm, loss = self.coverdcall_calculate(option_underlying_asset_price, 
                                                                            option_premium, 
                                                                            option_strike, 
                                                                            option_days_to_strike, 
                                                                            self.intrest_rate, tax_and_fee=tax_and_fee)
                    
                    # Calculate minimum option and capital we need to spend 
                    min_share_buy = 5000000 / option_underlying_asset_price 
                    if min_share_buy <= 1000:
                        min_option = 1
                        min_cap = 1000 * option_underlying_asset_price
                    else:
                        min_option = min_share_buy / 1000
                        min_cap = min_share_buy * option_underlying_asset_price


                    if year_p > 30:
                        data = {"symbol": self.option_df.iloc[i]['نماد'], 
                                "name": self.option_df.iloc[i]['نام'], 
                                "yp": year_p, "mp": month_p, "otm": otm, "loss": loss,
                                "min_op": min_option, "min_cap": min_cap}

                        # Add the dictionary as a new row in the DataFrame
                        update_coverdcall_filter_df = update_coverdcall_filter_df._append(data, ignore_index=True)

            if not coverdcall_filter_df.equals(update_coverdcall_filter_df):
                coverdcall_filter_df = update_coverdcall_filter_df
                print(update_coverdcall_filter_df)
                # Save the DataFrame to database
                Database().save_dataframe(self.df, 'coverdcall_data')

            # Clear the DataFrame, keeping the columns
            update_coverdcall_filter_df = update_coverdcall_filter_df[0:0]
            time.sleep(0.5)


#option().coverdcall_filter()

# Main function to run both tasks concurrently using threads
def main():
    # For checking if there is new option symbol
    tsetmc().update_all_data(repeat=1)

    # Create two threads: one for web scraping, one for processing the file
    thread1 = threading.Thread(target=tsetmc().update_all_data, kwargs={'just_option': True})
    thread2 = threading.Thread(target=option().coverdcall_filter)

    # Start both threads
    thread1.start()
    thread2.start()

    # Wait for both threads to complete
    thread1.join()
    thread2.join()


# Run the main function
if __name__ == "__main__":
    main()



