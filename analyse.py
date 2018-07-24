#! analyse.py
"""Analyse applications from CSV file"""

from pathlib import Path
import pandas as pd
from datetime import datetime, date
import sys

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
                            "name",
                            "gender",
                            "birthDate",
                            "age",
                            "nationality",
                            "postalAddress",
                            "country",
                            "emailAddress",
                            "phoneNumber",
                            "course",
                            "cseeYear",
                            "oLevelNumber",
                            "biology",
                            "chemistry",
                            "physics",
                            "maths",
                            "english",
                            "code",
                            "how"
                        ]

    # For aesthetic purposes
    dataframe["name"] = dataframe["name"].apply(lambda x: x.upper())

    # Making sure that name comparison will work by removing leading, extra and trailing spaces
    dataframe["name"] = dataframe["name"].apply(lambda x: ' '.join(x.split()))

    # This goes after columns renaming as it depend on new renaming, 'oLevelNumber'
    # oLevelNumber seem to be more unique even in spelling.
    # There are still cases where oLevelNumber does not work.
    dataframe = dataframe.drop_duplicates(subset=["oLevelNumber"])

    # Do a second pass of removing duplicates by checking 'names'
    dataframe = dataframe.drop_duplicates(subset=["name"])

    # Insert age, in years, column after calculating it from birth date
    dataframe.insert(3, 'age_calc', dataframe['birthDate'].apply(lambda x: calculate_age(x)))

    # To make it easy to detect repeatition when eye balling the Excel file
    dataframe = dataframe.sort_values(["name"], ascending=True)
    return dataframe


def split_courses(dataframe: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    """Split the dataframe into the three separate courses.

    Return a tuple with three dataframes."""

    ca_co_upgrading = dataframe.loc[dataframe["course"] == "Ordinary Diploma in Clinical Medicine (CA to CO upgrading, one year)"]
    resident_co = dataframe.loc[dataframe["course"] == "Ordinary Diploma in Clinical Medicine (fresh from school to become Clinical Officer, three years)"]
    his = dataframe.loc[dataframe["course"] == "Ordinary Diploma in Health Information Science (three years)"]

    return (ca_co_upgrading, resident_co, his)


def get_duplicates(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check for duplicates and return a dataframe with duplicates."""

    return dataframe[dataframe.duplicated(subset=["oLevelNumber"])]


def calculate_age(born: str) -> int:
    """Calculate the age based on the given birth date.

    Return age in years.
    """

    born = datetime.strptime(born, "%Y-%m-%d")
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def credit_c(score: str) -> str:
    """Check that the credit is C or above and return True, else return False."""

    possible_values = ['A', 'B', 'C']

    if score in possible_values:
        return "Yes"
    
    return "No"


def credit_d(score: str) -> str:
    """Check that the credit is D or above and return 'Yes', else return 'No'."""

    possible_values = ['A', 'B', 'C', 'D']

    if score in possible_values:
        return "Yes"
    
    return "No"


def check_qualification(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that a candidate qualify for a selected course.
    
    Return a dataframe with a column Qualify filled, with 'Yes' or 'No' accordingly."""

    dataframe["Qualify"] = ""

    for index, row in dataframe.iterrows():
        if row['course'] == "Ordinary Diploma in Clinical Medicine (fresh from school to become Clinical Officer, three years)":
            qualifications = [credit_c(row['biology']),
                              credit_c(row['chemistry']),
                              credit_d(row['physics']),
                              credit_d(row['maths']),
                              credit_d(row['english'])]

            if "No" in qualifications:
                dataframe.set_value(index,'Qualify', 'No')
            else:
                dataframe.set_value(index,'Qualify', 'Yes')

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
        splitted = split_courses(dataframe)

        # Excel file for writing the analysis results
        candidates_file = "candidates.xlsx"
        writer = pd.ExcelWriter(candidates_file)

        # Write the analysis summary in the first sheet
        CACO_males = (splitted[0][['gender']] == 'Male').sum()
        CACO_females = (splitted[0][['gender']] == 'Female').sum()
        rCO_males = (splitted[1][['gender']] == 'Male').sum()
        rCO_females = (splitted[1][['gender']] == 'Female').sum()
        HIS_males = (splitted[2][['gender']] == 'Male').sum()
        HIS_females = (splitted[2][['gender']] == 'Female').sum()

        summary_dictionary = {"CACO": [len(splitted[0]), int(CACO_males), int(CACO_females)],
                              "rCO": [len(splitted[1]), int(rCO_males), int(rCO_females)],
                              "HIS": [len(splitted[2]), int(HIS_males), int(HIS_females)]
                              }
        summary_df = pd.DataFrame.from_dict(summary_dictionary, orient='index')
        summary_df.columns = ['Count', 'Males', 'Females']
        summary_df.loc['Total']= summary_df.sum()
        summary_df.to_excel(writer, "Summary", freeze_panes=(1, 1))

        # Every course on its own sheet
        splitted[0].to_excel(writer, "CACO-candidates", freeze_panes=(1, 1))
        splitted[1].to_excel(writer, "rCO-candidates", freeze_panes=(1, 1))
        splitted[2].to_excel(writer, "HIS-candidates", freeze_panes=(1, 1))

        # For a quick picture of what is going on.
        print(summary_df)

        print(f"\n--> Data frames written to file '{candidates_file}'")

    else:
        print(f"\n--> File '{filename}' does not exists!\n")


# Run everything
if __name__ == "__main__":
    decorator = "*" * 60
    print(f'\n{decorator}')

    if len(sys.argv) == 1:
        print('\n--> You need to provide a full path to the csv file.\n')

    else:
        run(sys.argv[1])

    print(f'{decorator}\n')