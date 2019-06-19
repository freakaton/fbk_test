import re
import requests
import csv
from scrapy.selector import Selector


# TODO: Научится обрабатывать несколько имен в одном блоке
class SlovakiaParser:
    LIMIT = 10
    URL = "http://www.orsr.sk/vypis.asp?lan=en&ID={id}&SID={sid}&P=0"
    courts = [3, 2, 4, 9, 8, 6, 7, 5]
    exclude_data = ['Ing.', 'predstavenstva', 'From:']
    RUSSIA = 'Ruská'
    FIELDNAMES = ['company', 'name', 'address']

    def main(self):
        file = open('slovakia_names.csv', 'w', newline='')
        writer = csv.writer(file, delimiter=';')
        writer.writerow(self.FIELDNAMES)
        for i in range(self.LIMIT):
            for j in self.courts:
                url = self.URL.format(id=i, sid=j)
                print(url)
                resp = requests.get(url).content.decode('windows-1250')
                selector = Selector(text=resp)
                name_addresses = []
                if not self.is_right_page(selector):
                    continue

                company = self.parse_business_name(selector)
                name_addresses += self.parse_management_body(selector)
                name_addresses += self.parse_partners(selector)

                for name_address in name_addresses:
                    name_address = [re.sub(r'[",;]', '', n).strip() for n in name_address]
                    print("Found name: ", name_address)
                    writer.writerow([company] + name_address)
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
                    if not any(word in addr for word in cls.exclude_data):
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
                    if not any(word in addr for word in cls.exclude_data):
                        addr_str += addr.strip() + ", "
                ret.append([name, addr_str])
        return ret


parser = SlovakiaParser()
parser.main()
