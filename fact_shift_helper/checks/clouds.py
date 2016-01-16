# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
from . import Check

from ..tools.smartfact import TableCrawler

clouds_url = "http://catserver.ing.iac.es/weather/archive/concam/index.php"

class CloudCheck(Check):
    def check(self):
        print("Checking clouds")
        fmt = '{:2.1f}'
        text = TableCrawler(clouds_url).page_payload
        a = list(filter(lambda x: "Coverage: " in x, text))
        try:
            #ugliest way to do this ever. It seems to work though.
            coverage = int(a[0].split("Coverage: ")[1].split('%')[0])
            if coverage >= 0 and coverage < 50:
                self.update_system_status(
                    'cloud cover', fmt.format(coverage), '%'
                )
            else:
                raise ValueError
        except ValueError:
            mesg = "coverage >= 50 km/h: {:2.1f} %"
            self.queue.append(mesg.format(coverage))
