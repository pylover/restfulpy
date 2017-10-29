

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

| Operator  | Meaning | Example         |
| --------- | ------- | --------------- |
|           | =       | id=2            |
| !         | !=      | id=!2           |
| >         | >       | id=>2           |
| >=        | >=      | id=>=2          |
| <         | <       | id=<2           |
| <=        | <=      | id=<=2          |
| %         | LIKE    | title=u%s       |
| ~,%       | ILIKE   | title=~u%s      |
| IN()      | IN      | id=IN(2,3,4)    |
| !IN()     | NOT IN  | id=!IN(2,3,4)   |
| BETWEEN() | BETWEEN | id=BETWEEN(2,9) |


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
