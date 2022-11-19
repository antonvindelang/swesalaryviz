from openpyxl import load_workbook
import re
import csv


WB_FILE = 'data/csfvi---inkomstklasser-2020.xlsx' # Download from SCB https://www.scb.se/hitta-statistik/statistik-efter-amne/hushallens-ekonomi/inkomster-och-inkomstfordelning/inkomster-och-skatter/
HEADER = ['age_range', 'gender', 'income','min_income', 'max_income', 'number_of_people']
OUT_FILE = 'data/income_classes_processed.csv'

def make_csv(data):
    with open(OUT_FILE, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(HEADER)
        writer.writerows(data)

def process_workbook(filename):
    wb = load_workbook(filename=filename)
    sheet = wb.active

    age_range_cells = ['C6', 'G6', 'K6', 'O6',
                       'S6', 'W6', 'AA6', 'AE6', 'AI6', 'AM6']
    age_ranges = [sheet[cell].value.replace('–','-') for cell in age_range_cells]

    gender_classes_cells = ['C7', 'D7', 'E7']
    gender_classes = [sheet[cell].value for cell in gender_classes_cells]

    income_class_range = 'A11:A54'
    income_classes = [cell[0].value for cell in sheet[income_class_range]]
    income_classes = [re.sub('tkr', '', str(value).rstrip().replace('–', '-'))
                      for value in income_classes]

    start_x = 11
    start_y = 3

    data = []
    for age_i, age in enumerate(age_ranges):
        for gender_i, gender in enumerate(gender_classes):
            for income_i, income in enumerate(income_classes):
                value = sheet.cell(start_x + income_i,
                                   (start_y+gender_i) + (4*age_i)).value
                value = 0 if value == '..' else value
                if income == '0':
                    min_income = 0
                    max_income = 1
                elif income == '3 000-':
                    min_income = 3000
                    max_income = None
                else:
                    min_income, max_income = [int(re.sub("\D", "", x)) for x in income.split('-')]

                data.append((age, gender, income, min_income, max_income, value))

    return data


def main():
    data = process_workbook(WB_FILE)
    make_csv(data)


if __name__ == '__main__':
    main()
