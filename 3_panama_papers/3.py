import csv


def get_all_companies(file) -> dict:
    """
    1 Step

    Load companies from OCOD File
    :return: dict:
    {
        "Name of company": {
            Title_Number: <number:str>,
            Property_Address: <addr:str>,
        },
        ...
    }
    """
    db = csv.DictReader(file)
    companies = {}
    for row in db:
        name = row['Proprietor Name (1)']
        if name:
            company = dict()
            company['Title_Number'] = row['Title Number']
            company['Property_Address'] = row['Property Address']
            companies[row['Proprietor Name (1)'].strip().lower()] = company
    return companies


def check_for_company(file, companies: dict) -> list:
    """
    2 Step

    Find companies in Entities table of PP by name

    :param file:
    :param companies: dict: from 1 step
    :return: companies: list:
    [{
        Title_Number: <number:str>,
        Property_Address: <addr:str>,
        Node_Id: <node id:str>,
    }, ...]
    """
    checks = []
    db = csv.DictReader(file)
    for row in db:
        name = row['name'].strip().lower()
        check = companies.get(name, None)
        if check:
            check['Node_Id'] = row['node_id']
            check['Company_Name'] = row['name']
            checks.append(check)
    return checks


def _find_owner(node: str, db: dict):
    """
    find owner by id
    :param node: str:
    :param db: dict:
    :return: str or None
    """
    edge = db.get(node)
    if edge:
        if 'shareholder' in edge[1] or 'owner' in edge[1]:
            return edge[0]
        elif edge[1] in 'intermediary of':
            return _find_owner(edge[0], db)
        else:
            return None


def find_owner_ids(file, companies: list) -> list:
    """
    3 Step Recursively searching of owner_id in edges table

    :param file:
    :param companies:
    :return: list:
    [{
        Title_Number: <number:str>,
        Property_Address: <addr:str>,
        Node_Id: <node id:str>,
        Owner: <owner id: str>
    }, ...]
    """
    db = csv.DictReader(file)
    dict_db = {}
    for row in db:
        dict_db[row['END_ID']] = (row["START_ID"], row['link'])
    for company in companies:
        company['Owner'] = _find_owner(company['Node_Id'], dict_db)
    return companies


def find_names_by_id(file, ix_companies: dict):
    """
    4 Step Find in csv file names by id of company

    :param file:
    :param ix_companies: dict: {<owner id:str>: {dict of company}}
    :return: dict: {<owner id:str>: {dict of company}}
    """
    db = csv.DictReader(file)
    for row in db:
        company = ix_companies.get(row['node_id'])
        if company:
            company['Owner'] = row['name']
    return ix_companies


def main():
    with open('src/OCOD_FULL_2019_06.csv', 'r') as f:
        companies = get_all_companies(f)
    with open('src/Panama_papers/panama_papers.nodes.entity.csv', 'r') as f:
        companies = check_for_company(f, companies)
    with open('src/Panama_papers/panama_papers.edges.csv') as f:
        companies = find_owner_ids(f, companies)

    ix_companies = {}
    for company in companies:
        ix_companies[company['Owner']] = company

    with open('src/Panama_papers/panama_papers.nodes.entity.csv', 'r') as f:
        ix_companies = find_names_by_id(f, ix_companies)
    with open('src/Panama_papers/panama_papers.nodes.officer.csv', 'r') as f:
        ix_companies = find_names_by_id(f, ix_companies)

    companies = []
    # Prepare structure to dump in result file
    for k, v in ix_companies.items():
        del v['Node_Id']
        companies.append(v)

    with open('result.csv', 'w') as f:
        fieldnames = ['Title_Number', 'Property_Address', 'Company_Name', 'Owner']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(companies)


if __name__ == '__main__':
    main()