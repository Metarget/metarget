"""
Filters
"""


def filter_vuln_by_name(vulns, name):
    vuln = None
    for v in vulns:
        if v['name'].startswith(name):
            vuln = v
            break
    return vuln
