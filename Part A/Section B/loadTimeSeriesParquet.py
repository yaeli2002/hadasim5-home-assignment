#Parquet is a format that stores large datasets efficiently. It is optimized for fast queries and compression.
#It has interoperability – it allows easy transfer and processing of data between different tools and systems, reducing #dependency on specific vendors.
#It has accessibility – the format's specification is publicly available, so anyone can develop tools to read and write #the data, opening up many possibilities for analysis.
#Additionally, it is less prone to obsolescence because it is not tied to specific software, ensuring that the data #remains accessible over time.


import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

# A function that converts the timestamp column to a standard date and time format, and converts invalid date to NaN.
def convert_to_datetime(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', dayfirst=True)
    return df

# The function converts the values in the value column to numeric format, and converts invalid values to NaN.
def convert_to_number(df):
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df

# A function that removes rows with invalid values in the timestamp column or the value column, and returns the file with the correct lines.
def remove_invalid_rows(df):
    df = df.dropna(subset=['timestamp', 'value'])
    return df

# Clean dataframe in memory 
def dataframe_cleanup(df):
    df = convert_to_datetime(df)
    df = convert_to_number(df)
    df = remove_invalid_rows(df)
    df = df.drop_duplicates(subset=['timestamp'], keep=False)
    df = df.sort_values(by='timestamp')
    return df

# The function calculates the average of each hour on each date.
def average_for_each_hour(df):
    df['hour'] = df['timestamp'].dt.floor('h')
    return df.groupby('hour')['value'].mean().reset_index()

# The function reads time series data from Parquet, calculates hourly averages, and saves them to a CSV file.
def procces_data_by_hour(input_file, output_file):
    try:
        df = pd.read_parquet(input_file, columns=['timestamp', 'value'])
    except FileNotFoundError as e:
        logging.error(f"File not found: {input_file}. Exception: {e}")
        return
    except pd.errors.ParserError as e:
        logging.error(f"Error parsing the Parquet file: {input_file}. Exception: {e}")
        return
    except Exception as e:
        logging.error(f"Error reading the file: {e}")
        return

    # Clean and process in memory
    df = dataframe_cleanup(df)
    hourly_avg = average_for_each_hour(df)
    hourly_avg.rename(columns={'hour': 'זמן התחלה', 'value': 'ממוצע'}, inplace=True)
    hourly_avg['זמן התחלה'] = hourly_avg['זמן התחלה'].dt.strftime("%d/%m/%Y %H:%M:%S")

    try:
        hourly_avg.to_csv(output_file, index=False, encoding='utf-8-sig')
    except PermissionError as e:
        logging.error(f"Permission denied when saving to {output_file}: {e}")
    except OSError as e:
            logging.error(f"OS error when saving average file: {e}")
    except Exception as e:
        logging.error(f"Error saving average file: {e}")

def main():
    input_file = "time_series.parquet"
    output_file = "avarage_by_hours_parquet.csv"
    procces_data_by_hour(input_file, output_file)

if __name__ == "__main__":
    main()
