import pandas as pd
import logging
import os
import tempfile

logging.basicConfig(level=logging.INFO)


def convert_to_datetime(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', dayfirst=True)
    return df

#The function converts the values in the value column to numeric format, and converts invalid values to NaN.
def convert_to_number(df):
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df

def remove_invalid_rows(df):
    df = df.dropna(subset=['timestamp', 'value'])
    return df

def dataframe_cleanup(df):
    df = convert_to_datetime(df)
    df = convert_to_number(df)
    df = remove_invalid_rows(df)
    df = df.drop_duplicates(subset=['timestamp'], keep=False)
    df = df.sort_values(by='timestamp')
    return df

def average_for_each_hour(df):
    df['hour'] = df['timestamp'].dt.floor('h')
    return df.groupby('hour')['value'].mean().reset_index()

def split_by_day(df):
    df['date'] = df['timestamp'].dt.date
    grouped = df.groupby('date')
    file_list = []

    for date, group in grouped:
        group['timestamp'] = group['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', newline='', encoding='utf-8-sig')
        group.drop(columns='date').to_csv(temp_file.name, index=False)
        file_list.append(temp_file.name)
        temp_file.close()

    return file_list

def process_temp_file(file_path):
    df = pd.read_csv(file_path)
    df = dataframe_cleanup(df)
    hourly_avg = average_for_each_hour(df)
    return hourly_avg

def process_data_in_parts(input_file, final_output_file):
    try:
        df = pd.read_parquet(input_file, columns=['timestamp', 'value'])
    except FileNotFoundError as e:
        logging.error(f"File not found: {input_file}. Exception: {e}")
        return
    except pd.errors.ParserError as e:
        logging.error(f"Error parsing the Parquet file: {input_file}. Exception: {e}")
        return
    except Exception as e:
        logging.error(f"Error reading the Parquet file: {input_file}. Exception: {e}")
        return


    df = dataframe_cleanup(df)
    temp_files = split_by_day(df)
    all_parts = []

    for temp_file in temp_files:
        try:
            part_avg = process_temp_file(temp_file)
            all_parts.append(part_avg)
        finally:
            os.remove(temp_file)

    if all_parts:
        final_df = pd.concat(all_parts)
        final_df.rename(columns={'hour': 'זמן התחלה', 'value': 'ממוצע'}, inplace=True)
        final_df['זמן התחלה'] = final_df['זמן התחלה'].dt.strftime("%d/%m/%Y %H:%M:%S")
        try:
            final_df.to_csv(final_output_file, index=False, encoding='utf-8-sig')
        except PermissionError as e:
            logging.error(f"Permission denied when saving to {final_output_file}: {e}")
        except OSError as e:
            logging.error(f"OS error when saving average file: {e}")
        except Exception as e:
            logging.error(f"Error saving average file: {e}")

def main():
    input_file = "time_series.parquet"
    final_output = "avarage_by_hours_split_parquet.csv"
    process_data_in_parts(input_file, final_output)

if __name__ == "__main__":
    main()
