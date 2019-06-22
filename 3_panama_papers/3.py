import csv


def get_all_companies(file):
    gb_db = csv.DictReader(file)
    companies = {}

    for row in gb_db:
        name = row['Proprietor Name (1)']
        if name:
            company = dict()
            company['Title_Number'] = row['Title Number']
            company['Property_Address'] = row['Property Address']
            companies[row['Proprietor Name (1)'].strip().lower()] = company
    return companies


def check_for_company(file, companies):
    checks = []
    db = csv.DictReader(file)
    for row in db:
        name = row['name'].strip().lower()
        check = companies.get(name, None)
        if check:
            check['Node_Id'] = row['node_id']
            check['Company_Name'] = row['name']
            check['Owner'] = ''
            checks.append(check)
    return checks


def find_owner_ids(file, companies):
    db = csv.DictReader(file)
    owner_statuses = {'shareholder', 'owner'}
    intermediary = 'intermediary of'
    ids = {cp['Node_Id'] for cp in companies}
    resp = dict()
    for id in ids:
        resp[id] = []

    for row in db:
        if row["END_ID"] in ids:
            if row['link'] in owner_statuses:
                resp[row["END_ID"]] = row['START_ID']
            elif row['link'] == intermediary:
                pass
            # TODO: Доделать
    return resp

def main():
    with open('src/OCOD_FULL_2019_06.csv', 'r') as f:
        companies = get_all_companies(f)
    with open('src/Panama_papers/panama_papers.nodes.entity.csv', 'r') as f:
        companies = check_for_company(f, companies)
    with open('src/Panama_papers/panama_papers.edges.csv') as f:
        owner_ids = find_owner_ids(f, companies)
    with open('result.csv', 'w') as f:
        fieldnames = ['Title_Number', 'Property_Address', 'Company_Name', 'Owner', 'Node_Id']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(companies)


if __name__ == '__main__':
    main()