# Copyright (c) 2024 Vincent Danen
# License: GPLv3+

from .constants import (
    filter_products,
    VENDOR_ADVISORY,
)

def product_lookup(product, pmap):
    # lookup the product name by identifier
    for x in pmap:
        if product in x.keys():
            return x[product]

class Fix(object):
    """
    class to handle vendor fixes
    """

    def __init__(self, x, pmap):
            self.id = None
            self.url = x['url']
            self.components = []

            for v in VENDOR_ADVISORY:
                if v in self.url:
                    # TODO: some regexp here to make this better; right now I'm assuming RHSA
                    self.id = self.url.split('/')[-1]

            for y in filter_products(x['product_ids']):
                (product, component, version) = y.split(':')
                self.components.append(':'.join([component, version]))
                self.product = product_lookup(product, pmap)

class VexPackages(object):
    """
    class to handle packages
    """

    def __init__(self, vexdata):
        self.raw = vexdata
        self.build_product_tree()
        self.parse_packages()

    def build_product_tree(self):
        """
        Parse included packages
        :return:
        """

        self.pmap = []
        for p in self.raw['product_tree']['branches']:
            # TODO there seems to be a bug in the VEX output respective to branch nesting, it's very convoluted =(
            for b in p['branches']:
                if 'category' in b.keys():
                    if b['category'] == 'product_name':
                        name = b['name']
                        id = b['product']['product_id']
                        self.pmap.append({id: name})

                # this is where the bug is, we shouldn't have to step down a level when the first product is one level up, right?
                if 'branches' in b.keys():
                    for c in b['branches']:
                        if 'category' in c.keys():
                            if c['category'] == 'product_name':
                                name = c['name']
                                id = c['product']['product_id']
                                self.pmap.append({id: name})

    def parse_packages(self):
        # errata
        self.fixes       = []
        self.workarounds = []
        self.wontfix     = []
        for k in self.raw['vulnerabilities']:
            for x in k['remediations']:
                if x['category'] == 'vendor_fix':
                    self.fixes.append(Fix(x, self.pmap))

                if x['category'] == 'workaround':
                    wa_details = x['details']
                    # seems stupid to have a package list for workarounds
                    # but... just in case
                    w_pkgs = filter_products(x['product_ids'])
                    self.workarounds.append({'details': wa_details, 'packages': w_pkgs})

                if x['category'] == 'no_fix_planned':
                    nf_details = x['details']
                    for p in x['product_ids']:
                        self.wontfix.append({'product': p, 'reason': nf_details})
