import csv


def check_for_company(file, companies):
    checks = []
    db = csv.DictReader(file)
    for row in db:

        if row['name'].strip().lower() in companies.keys():
            checks.append(row)
    return checks


def get_all_companies(file):
    gb_db = csv.DictReader(file)
    companies = {}

    for row in gb_db:
        name = row['Proprietor Name (1)']
        if name:
            companies[name.strip().lower()] = row
    return companies


if __name__ == '__main__':
    with open('src/OCOD_FULL_2019_06.csv', 'r') as f:
        companies = get_all_companies(f)
    with open('src/Panama_papers/panama_papers.nodes.entity.csv', 'r') as f:
        checks = check_for_company(f, companies)
        import pdb
        pdb.set_trace()