"""
Deal with table in command line
"""

from prettytable import PrettyTable


def show_table(obj_list, sort_key=None, sortby=None):
    x = PrettyTable()

    if len(obj_list) == 0:
        return

    x.field_names = list(obj_list[0].keys())
    x.align = 'l'

    for obj in obj_list:
        x.add_row(list(obj.values()))

    nl_print(x.get_string(sort_key=sort_key, sortby=sortby))


def nl_print(msg):
    """
    print with a new line :)
    :param msg:
    :return:
    """
    print(str(msg) + "\n")


if __name__ == '__main__':
    sample = [{'name': 'cve-2019-14271',
               'class': 'docker',
               'type': 'container_escape'},
              {'name': 'cve-2018-15664',
               'class': 'docker',
               'type': 'container_escape'},
              {'name': 'cve-2019-13139',
               'class': 'docker',
               'type': 'command_execution'},
              {'name': 'cve-2020-15257',
               'class': 'docker',
               'type': 'container_escape'},
              {'name': 'cve-2019-5736',
               'class': 'docker',
               'type': 'container_escape'}]
    show_table(sample, 'class')
