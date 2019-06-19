import re
import csv
import requests
import time
from multiprocessing import Pool

from scrapy.selector import Selector


# TODO: Научится обрабатывать несколько имен в одном блоке
class SlovakiaParser:
    LIMIT = 20
    RANGE = 10
    URL = "http://www.orsr.sk/vypis.asp?lan=en&ID={id}&SID={sid}&P=0"
    COURTS = [3, 2, 4, 9, 8, 6, 7, 5]
    EXCLUDE_DATA = ['Ing.', 'predstavenstva', 'From:']
    RUSSIA = 'Ruská'
    FIELDNAMES = ['company', 'name', 'address']

    @classmethod
    def url_generator(cls, from_range: int):
        for i in range(from_range, from_range + cls.RANGE):
            for j in cls.COURTS:
                yield cls.URL.format(id=i, sid=j)

    def parse_url(self, url: str):
        time.sleep(0.1)
        resp = requests.get(url, timeout=10).content.decode('windows-1250')
        selector = Selector(text=resp)
        name_addresses = []
        if not self.is_right_page(selector):
            return []

        company = self.parse_business_name(selector)
        name_addresses += self.parse_management_body(selector)
        name_addresses += self.parse_partners(selector)

        ret = []
        for name_address in name_addresses:
            name_address = [re.sub(r'[",;]', '', n).strip() for n in name_address]
            print("Found name: ", name_address)
            is_russian = self.RUSSIA in name_address[1]
            ret.append([re.sub(r'[",;]', '', company).strip()] + name_address + [is_russian])
        return ret

    def main(self):
        file = open('slovakia_names.csv', 'w', newline='')
        writer = csv.writer(file, delimiter=';')
        writer.writerow(self.FIELDNAMES)

        rfile = open('russian_slovakia_names.csv', 'w', newline='')
        rwriter = csv.writer(rfile, delimiter=';')
        rwriter.writerow(self.FIELDNAMES)

        pool = Pool(10)
        for i in range(0, self.LIMIT, self.RANGE):
            if i != 0:
                time.sleep(5)
            result = pool.map(self.parse_url, self.url_generator(i))
            print(f'loading pages from {i} to {i+self.RANGE-1}')
            import pdb
            pdb.set_trace()
            for names in result:
                if len(names):
                    for name in names:
                        if name[-1]:
                            rwriter.writerow(name[:-1])
                        writer.writerow(name[:-1])
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
        tables = selector.xpath("//tr[contains(.//td/span/text(), 'Partners')]/td[2]/table//td[@width='67%']")
        ret = []
        for table in tables:
            if len(table.xpath('.//a')) > 0:
                name = table.xpath('.//a/span/text()').getall()
                name = ' '.join(map(lambda n: n.strip(), name))
                addr_str = ''
                address = table.xpath('./span/text()').getall()
                for addr in address:
                    if not any(word in addr for word in cls.EXCLUDE_DATA):
                        addr_str += addr.strip() + ", "
                ret.append([name, addr_str])
        return ret

    @classmethod
    def parse_management_body(cls, selector: Selector):
        tables = selector.xpath("//tr[contains(.//td/span/text(), 'Management body')]/td[2]/table//td[@width='67%']")
        ret = []
        for table in tables:
            if len(table.xpath('.//a')) > 0:
                name = table.xpath('.//a/span/text()').getall()
                name = ' '.join(map(lambda n: n.strip(), name))
                addr_str = ''
                address = table.xpath('./span/text()').getall()
                for addr in address:
                    if not any(word in addr for word in cls.EXCLUDE_DATA):
                        addr_str += addr.strip() + ", "
                ret.append([name, addr_str])
        return ret


parser = SlovakiaParser()
parser.main()
