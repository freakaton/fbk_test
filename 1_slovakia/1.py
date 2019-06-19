import re
import requests
import csv
from scrapy.selector import Selector

# TODO: Научится обрабатывать несколько имен в одном блоке
class SlovakiaParser:
    LIMIT = 30
    companies = 0
    URL = "http://www.orsr.sk/vypis.asp?lan=en&ID={id}&SID={sid}&P=0"
    courts = [3, 2, 4, 9, 8, 6, 7, 5]
    date_regex = re.compile(r': \d{2}/\d{2}/\d{4}')
    FIELDNAMES = ['company', 'name', 'address']

    def main(self):
        file = open('slovakia_names.csv', 'w', newline='')
        writer = csv.DictWriter(file, delimiter=';', fieldnames=self.FIELDNAMES)
        for i in range(self.LIMIT):
            for j in self.courts:
                url = self.URL.format(id=i, sid=j)
                print(url)
                resp = requests.get(url).content.decode('windows-1250')
                selector = Selector(text=resp)
                names = []
                if not self.is_right_page(selector):
                    continue
                try:
                    company = self.parse_business_name(selector)
                except Exception as e:
                    print(e)
                    continue
                try:
                    names += self.parse_managment_body(selector)
                except Exception as e:
                    print(e)
                    pass
                try:
                    names += self.parse_partners(selector)
                except Exception as e:
                    print(e)
                    pass
                for name in names:
                    names = map(lambda n: re.sub(';', '', n), names)
                    row = dict(zip(self.FIELDNAMES, [company, name[0], name[1]]))
                    print("Found name: ", row)
                    writer.writerow(row)
        file.close()

    @classmethod
    def is_right_page(cls, selector: Selector):
        if selector.xpath("//h3[contains(.//text(), 'Last updating of databases')]"):
            return False
        else:
            return True

    @classmethod
    def parse_business_name(cls, selector: Selector):
        name = selector.xpath(
            "//tr[contains(.//span/text(), 'Business name')]/td[2]//td[@width='67%']//span/text()").getall()
        return name[0].strip()

    @classmethod
    def parse_partners(cls, selector: Selector):
        info = selector.xpath(
            "//tr[contains(.//td/span/text(), 'Partners')]/td[2]//td[@width='67%']//span/text()").getall()
        if not info:
            return []
        name = info[0].strip() + " " + info[1].strip()
        address = ""
        for i in info[2:]:
            if not cls.date_regex.findall(i):
                address += " " + i.strip()
        return [[name, address]]

    @classmethod
    def parse_managment_body(cls, selector: Selector):
        info = selector.xpath(
            "//tr[contains(.//td/span/text(), 'Management body')]/td[2]//td[@width='67%']//span/text()").getall()
        if not info:
            return []
        name = info[1].strip() + " " + info[2].strip()
        address = ""
        for i in info[3:]:
            if not cls.date_regex.findall(i):
                address += " " + i.strip()
        return [[name, address]]


parser = SlovakiaParser()
parser.main()
