

DOC_HEADER = """

| Parameter | Value       |
| --------- | ----------- |
| Author    | TestEngine  |
| Version   | %(version)s |
| Status    | Implemented |

"""


DOC_LEGEND = """

#### Legend


##### Paging

| Param  | Meaning            |
| ------ | ------------------ |
| take   | Rows per page      |
| skip   | Skip N rows        |


##### Search & Filtering

You can search and filter the result via query-string:

        /path/to/resource?field=[op]value1[,value2]

| Operator  | Meaning | Example    |
| --------- | ------- | -----------|
|           | =       | id=2       |
| !         | !=      | id=!2      |
| >         | >       | id=>2      |
| >=        | >=      | id=>=2     |
| <         | <       | id=<2      |
| <=        | <=      | id=<=2     |
| %         | LIKE    | title=%us  |
| %~        | ILIKE   | title=%~us |
| ^         | IN      | id=^2,3,4  |
| !^        | NOT IN  | id=!^2,3,4 |
| ~         | BETWEEN | id=~2,9    |


##### Sorting

You can sort like this:


        /path/to/resource?sort=[op]value


| Operator  | Meaning |
| --------- | ------- |
|           | ASC     |
| \-        | DESC    |

"""


class As:
    anonymouse = 'Anonymouse'
    member = 'Member'
    admin = 'Admin'
