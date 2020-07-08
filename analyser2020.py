#! analyse.py
"""Analyse applications from CSV file."""

from os import write
from pathlib import Path
import pandas as pd
from datetime import datetime, date
import sys
import shutil


# TODO: Split the function into three different functions:
# Function 1: read CSV??
# Function 2: Assign new column names into the data frame and return the dataframe
# Function 3: remove duplicates
def read_data_file(csv_datafile: str) -> pd.DataFrame:
    """Read the CSV data file, assign new column names to the dataframe and
    remove duplicates.

    Return Pandas dataframe."""

    dataframe = pd.read_csv(csv_datafile, index_col=0)

    # Change column names for easy of processing
    dataframe.columns = [\
                            
                            'first_name',
                            'second_name',
                            'surname',
                            'birth_date',
                            'age',
                            'gender',
                            'nationality',
                            'disability',
                            'form4index',
                            'form4year',
                            'physics',
                            'chemistry',
                            'biology',
                            'maths',
                            'english',
                            'form6index',
                            'form6year',
                            'phone',
                            'email',
                            'postal_address',
                            'region',
                            'district',
                            'next of kin name',
                            'next of kin phone number',
                            'next of kin address',
                            'next of kin relation',
                            'next of kin region of domicile',
                            'NTA level 4 registration number',
                            'NTA level 4 grade year',
                            'NTA level 5 registration number',
                            'NTA level 5 grade year'
                        ]

    # For aesthetic purposes
    dataframe["first_name"] = dataframe["first_name"].apply(lambda x: x.upper())
    dataframe["second_name"] = dataframe["second_name"].apply(lambda x: x.upper())
    dataframe["surname"] = dataframe["surname"].apply(lambda x: x.upper())

    # Making sure that name comparison will work by removing leading, extra and trailing spaces
    dataframe["first_name"] = dataframe["first_name"].apply(lambda x: ' '.join(x.split()))
    dataframe["second_name"] = dataframe["second_name"].apply(lambda x: ' '.join(x.split()))
    dataframe["surname"] = dataframe["surname"].apply(lambda x: ' '.join(x.split()))

    dataframe = create_full_name(dataframe)
    dataframe = dataframe.drop_duplicates(subset=['full_name'])

    # Insert age, in years, column after calculating it from birth date
    #dataframe.insert(3, 'age_calc', dataframe['birthDate'].apply(lambda x: calculate_age(x)))

    # To make it easy to detect repeatition when eye balling the Excel sheet.
    dataframe = dataframe.sort_values(["first_name"], ascending=True)
    return dataframe


def create_full_name(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Create full name columns"""

    dataframe.insert(3, 'full_name', '')

    for index, row in dataframe.iterrows():
        fullname = row['first_name'] + ' ' + row['second_name'] + ' ' + row['surname']
        dataframe.at[index, 'full_name'] = fullname
    
    return dataframe


def calculate_age(born: str) -> int:
    """Calculate the age based on the given birth date.

    Return age in years.
    """

    born = datetime.strptime(born, "%Y-%m-%d")
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def check_qualification(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that a candidate qualify for a selected course.
    
    Return a dataframe with a column 'Qualify' filled, with 'Yes' or 'No' accordingly.
    """

    # Empty column for specifying wheather a candidate qualifies.
    dataframe["Qualify"] = ""

    # Acceptable grades.
    # F is not accepted.
    grades = ['A', 'B', 'C', 'D']

    for index, row in dataframe.iterrows():
        if row['biology'] in grades and row['chemistry'] in grades and row['physics'] in grades:
            dataframe.at[index, 'Qualify'] = 'Yes'
            # dataframe.set_value(index, 'Qualify', 'Yes')
        else:
            dataframe.at[index, 'Qualify'] = 'No'
            # dataframe.set_value(index,'Qualify', 'No')

    return dataframe


def write_to_file(filename: str, sheet: str, dataframe: pd.DataFrame):
    """Writes the contents of a data frame into an excel file."""

    writer = pd.ExcelWriter(filename)
    dataframe.to_excel(writer, sheet)
    writer.save()
    print(f'*** Written to {filename} ***', filename)


def run(filename: str):
    """Read data from file, remove duplicates, split into different courses save as Excel files"""

    data_file_path = Path(filename)

    if data_file_path.exists():
        dataframe = read_data_file(data_file_path)
        dataframe = check_qualification(dataframe)

        # Excel file for writing the analysis results
        candidates_file = "candidates.xlsx"
        writer = pd.ExcelWriter(candidates_file)

        # Write the analysis summary in the first sheet
        males_count = (dataframe['gender'] == 'Male').sum()
        females_count = (dataframe['gender'] == 'Female').sum()
        summary_dict = {"Candidates": [len(dataframe), int(males_count), int(females_count)]}
        summary_df = pd.DataFrame.from_dict(summary_dict, orient='index')
        summary_df.columns = ['Total', 'Males', 'Females']
        summary_df.to_excel(writer, 'Summary', freeze_panes=(1, 1))
        
        # The details sheet
        dataframe.to_excel(writer, 'Applicants', freeze_panes=(1, 1))

        # Save the writer
        writer.save()

        # For a quick picture of what is going on.
        print(summary_df)

        print(f"\n\nData frame has been written to the file '{candidates_file}'")

    else:
        print(f"\nFile '{filename}' does not exists!\n")


# Run everything
if __name__ == "__main__":
    columns, rows = shutil.get_terminal_size(fallback=(80, 24))
    decorator = "*" * columns
    print(f'\n{decorator}')

    if len(sys.argv) == 1:
        print('\n--> You need to provide a full path to the csv file.\n')
    else:
        print('analysing ...\n\n')
        run(sys.argv[1])
        print("done!")
    
    print(f'{decorator}\n')