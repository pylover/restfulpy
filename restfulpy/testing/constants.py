

DOC_HEADER = """

[Author]: <TestEngine>
[Version]: <%(version)s>
[Status]: <Implemented>

"""


DOC_LEGEND = """

Legend
======

Paging
------

| Param  | Meaning            |
| ------ | ------------------ |
| limit  | Rows per page      |
| offset | Skip N rows        |


Search & Filtering
------------------

You can search and filter the result via query-string:

        /path/to/resource?field=[op]value

| Operator  | Meaning |
| --------- | ------- |
|           | =       |
| !         | !=      |
| >         | >       |
| >=        | >=      |
| <         | <       |
| <=        | <=      |
| %%        | LIKE    |
| ^         | IN      |
| !^        | NOT IN  |


Sorting
-------

You can sort like this:


        /path/to/resource?sort=[op]value


| Operator  | Meaning |
| --------- | ------- |
|           | ASC     |
| \-        | DESC    |

"""


class As:
    Anonymouse = 'Visitor'
    member = 'Member'
    admin = 'Admin'
    everyone = '%s|%s|%s' % (Anonymouse, member, admin)
