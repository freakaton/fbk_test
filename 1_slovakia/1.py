import re
import csv
import sys
import requests
import time
from multiprocessing import Pool

from scrapy.selector import Selector


class SlovakiaParser:
    LIMIT = 50000
    RANGE = 10
    URL = "http://www.orsr.sk/vypis.asp?lan=en&ID={id}&SID={sid}&P=0"
    COURTS = [3, 2, 4, 9, 8, 6, 7, 5]
    EXCLUDE_DATA = ['Ing.', 'predstavenstva', 'From:']
    RUSSIA = 'Ruská'
    FIELDNAMES = ['company', 'name', 'address']
    current_id = 0

    @classmethod
    def url_generator(cls, from_range: int):
        for i in range(from_range, from_range + cls.RANGE):
            for j in cls.COURTS:
                yield cls.URL.format(id=i, sid=j)

    def parse_url(self, url: str):
        time.sleep(0.1)
        resp = requests.get(url, timeout=5).content.decode('windows-1250')
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

    def main(self, start_id=0):
        file = open(f'slovakia_names_{start_id}.csv', 'w', newline='')
        writer = csv.writer(file, delimiter=';', quotechar='"')

        rfile = open(f'russian_slovakia_names_{start_id}.csv', 'w', newline='')
        rwriter = csv.writer(rfile, delimiter=';', quotechar='"')
        if not start_id:
            writer.writerow(self.FIELDNAMES)
            rwriter.writerow(self.FIELDNAMES)

        pool = Pool(6)
        for i in range(start_id, self.LIMIT, self.RANGE):
            self.current_id = i
            result = pool.map(self.parse_url, self.url_generator(i))
            print(f'loading pages from {i} to {i+self.RANGE-1}')
            for names in result:
                if len(names):
                    for name in names:
                        if name[-1]:
                            rwriter.writerow(name[:-1])
                        writer.writerow(name[:-1])
            file.flush()
            rfile.flush()
            time.sleep(1.5)

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


if __name__ == '__main__':
    parser = SlovakiaParser()
    if len(sys.argv) > 1 and sys.argv[1] == '--start_from':
        start_from = int(sys.argv[2])
    else:
        start_from = 0
    while True:
        try:
            parser.main(start_from)
        except KeyboardInterrupt:
            print("Ended at", parser.current_id)
            sys.exit()
        except:
            start_from = parser.current_id