"""
Implemented based on ``rfc6902`` for sqlalchemy models.


Commands:

Add
{"op": "add", "path": "/biscuits/1", "value": {"name": "Ginger Nut"}}
Adds a value to an object or inserts it into an array. In the case of an array the value is inserted before the given
index. The - character can be used instead of an index to insert at the end of an array.

Remove
{"op": "remove", "path": "/biscuits"}
Removes a value from an object or array.

Replace
{"op": "replace", "path": "/biscuits/0/name", "value": "Chocolate Digestive"}
Replaces a value. Equivalent to a “remove” followed by an “add”.

Copy
{"op": "copy", "from": "/biscuits/0", "path": "/best_biscuit"}
Copy a value from one location to another within the JSON document. Both from and path are JSON Pointers.

Move
{"op": "move", "from": "/biscuits", "path": "/cookies"}
Move a value from one location to the other. Both from and path are JSON Pointers.

Test
{"op": "test", "path": "/best_biscuit/name", "value": "Choco Leibniz"}
Tests that the specified value is set in the document. If the test fails then the patch as a whole should not apply.

References:

- https://tools.ietf.org/html/rfc6902
- http://jsonpatch.com

"""
