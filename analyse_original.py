# analyse.py
"""Analyse applications from CSV file"""

from pathlib import Path
import pandas as pd
from datetime import datetime, date

# TODO: Split the function into three different functions:
# Function 1: read CSV??
# Function 2: Assign new column names into the data frame and return the dataframe
# Function 3: remove duplicates
def read_data_file(csv_datafile):
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

    # This goes after after columns renaming as it depend on new renaming, 'oLevelNumber'
    # oLevelNumber seem to be more unique even in spelling.
    # There are still cases where oLevelNumber does not work.
    dataframe = dataframe.drop_duplicates(subset=["oLevelNumber"])

    # Do a second pass of removing duplicates by checking 'names'
    dataframe = dataframe.drop_duplicates(subset=["name"])

    # Insert age, in years, column after calculating it from birth date
    dataframe.insert(3, 'age_calc', dataframe['birthDate'].apply(lambda x: calculate_age(x)))

    # To make easy to detect repeatition
    dataframe = dataframe.sort_values(["name"], ascending=True)
    return dataframe


def split_courses(dataframe):
    """Split the dataframe into the three separate courses.

    Return a tuple with three dataframes."""

    ca_co_upgrading = dataframe.loc[dataframe["course"] == "Ordinary Diploma in Clinical Medicine (CA to CO upgrading, one year)"]
    resident_co = dataframe.loc[dataframe["course"] == "Ordinary Diploma in Clinical Medicine (fresh from school to become Clinical Officer, three years)"]
    his = dataframe.loc[dataframe["course"] == "Ordinary Diploma in Health Information Science (three years)"]

    return (ca_co_upgrading, resident_co, his)


def get_duplicates(dataframe):
    """Check for duplicates and return a dataframe with duplicates."""

    return dataframe[dataframe.duplicated(subset=["oLevelNumber"])]


def calculate_age(born):
    """Calculate the age based on the given birth date.

    Return age in years.
    """

    born = datetime.strptime(born, "%Y-%m-%d")
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def credit_c(score):
    """Check that the credit is C or above and return True, else return False."""

    possible_values = ['A', 'B', 'C']

    if score in possible_values:
        return "Yes"
    
    return "No"

def credit_d(score):
    """Check that the credit is D or above and return 'Yes', else return 'No'."""

    possible_values = ['A', 'B', 'C', 'D']

    if score in possible_values:
        return "Yes"
    
    return "No"


def check_qualification(dataframe):
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


def write_to_file(filename, sheet, dataframe):
    """Writes the contents of a data frame into an excel file."""

    writer = pd.ExcelWriter(filename)
    dataframe.to_excel(writer, sheet)
    writer.save()
    print(f'*** Written to {filename} ***', filename)


def run():
    """Read data from file, remove duplicates, split into different courses save as Excel files"""

    data_file = "../23_july_2018_m/applications.csv"
    data_file_path = Path(data_file)

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

        print(f"--> Data frames written to file {candidates_file}.")

    else:
        print(f"File {data_file} does not exists!")


# Make it possible for the script to run on itself in case no modification and testing is
# needed.
if __name__ == "__main__":
    run()