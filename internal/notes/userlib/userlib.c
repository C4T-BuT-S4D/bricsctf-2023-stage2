#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>

#include <Python.h>
#include "structmember.h"


char is_valid_letter(char c) {
    return ('0' <= c && c <= '9') || ('a' <= c && c <= 'z') || ('A' <= c && c <= 'Z');
}

char is_valid_string(char *s) {
    if (!(strlen(s) > 4 && strlen(s) < 32)) return 0;

    for (int i = 0; i < strlen(s); ++i) {
        if (!is_valid_letter(s[i])) return 0;
    }
    return 1;
}

PyObject *userlib_is_valid_string(PyObject *self, PyObject *args) {
    char *str;
    if (!PyArg_ParseTuple(args, "s", &str)) {
        return NULL;
    }
    if (!is_valid_string(str)) Py_RETURN_FALSE;
    Py_RETURN_TRUE; 
}

PyObject *userlib_validate_creds(PyObject *self, PyObject *args) {
    char *name, *pass;
    if (!PyArg_ParseTuple(args, "ss", &name, &pass)) {
        return NULL;
    }
    if (!is_valid_string(name)) Py_RETURN_FALSE;
    if (!is_valid_string(pass)) Py_RETURN_FALSE;
    Py_RETURN_TRUE; 
}

char *get_path(char *username) {
    char *path = malloc(0x40);
    memset(path, 0, 0x40);
    strcpy(path, "./storage/");
    strcat(path, username);
    return path;
}

PyObject *userlib_user_exists(PyObject *self, PyObject *args) {
    char *username;
    if (!PyArg_ParseTuple(args, "s", &username)) {
        return NULL;
    }
    char *path = get_path(username);
    int exists = !access(path, R_OK|W_OK);
    free(path);
    if (exists) Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

PyObject *userlib_check_password(PyObject *self, PyObject *args) {
    char *name, *pass;
    if (!PyArg_ParseTuple(args, "ss", &name, &pass)) {
        return NULL;
    }
    char *path = get_path(name);
    FILE *f = fopen(path, "r");

    char correct_pass[0x40] = {};
    int pass_len = 0;
    fread(&pass_len, sizeof(int), 1, f);
    fread(correct_pass, pass_len, 1, f);
    fclose(f);
    free(path);
    if (!strcmp(pass, correct_pass)) Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

PyObject *userlib_store_new_user(PyObject *self, PyObject *args) {
    char *username, *password;
    if (!PyArg_ParseTuple(args, "ss", &username, &password)) {
        return NULL;
    }
    char *path = get_path(username);
    FILE *f = fopen(path, "w");
    int pass_len = strlen(password);
    fwrite(&pass_len, sizeof(int), 1, f);
    fwrite(password, pass_len, 1, f);
    int _0 = 0;
    fwrite(&_0, sizeof(int), 1, f);
    fwrite(&_0, sizeof(int), 1, f);
    fwrite(&_0, sizeof(int), 1, f);
    fwrite(&_0, sizeof(int), 1, f);
    fclose(f);
    free(path);
    Py_RETURN_NONE;
}

typedef struct {
    PyObject_HEAD
    PyObject *username;
    PyObject *password;
    PyObject *secret_note;
    PyObject *key;
    PyObject *notes;
    PyObject *notes_info;
    PyObject *shared_notes;
    PyObject *shared_notes_info;
} UserObject;

static void User_dealloc(UserObject *self) {
    const char *username = PyUnicode_AsUTF8(self->username);
    char *path = get_path(username);
    FILE *f = fopen(path, "w");
    free(path);

    const char *password = PyUnicode_AsUTF8(self->password);
    int pass_len = strlen(password);
    fwrite(&pass_len, sizeof(int), 1, f);
    fwrite(password, pass_len, 1, f);

    int secret_note_sz = PyByteArray_Size(self->secret_note);
    char *secret_note = PyByteArray_AsString(self->secret_note);
    fwrite(&secret_note_sz, sizeof(int), 1, f);
    fwrite(secret_note, secret_note_sz, 1, f);

    int key_len = PyByteArray_Size(self->key);
    char *key = PyByteArray_AsString(self->key);
    fwrite(&key_len, sizeof(int), 1, f);
    fwrite(key, key_len, 1, f);

    int notes_sz;
    notes_sz = PyList_Size(self->notes);
    fwrite(&notes_sz, sizeof(int), 1, f);
    PyObject *obj;
    int obj_len;
    const char *obj_str;
    for (int i = 0; i < notes_sz; ++i) {
        obj = PyList_GetItem(self->notes, i);
        obj_str = PyUnicode_AsUTF8(obj);
        obj_len = strlen(obj_str);
        fwrite(&obj_len, sizeof(int), 1, f);
        fwrite(obj_str, obj_len, 1, f);

        obj = PyList_GetItem(self->notes_info, i);
        obj_str = PyUnicode_AsUTF8(obj);
        obj_len = strlen(obj_str);
        fwrite(&obj_len, sizeof(int), 1, f);
        fwrite(obj_str, obj_len, 1, f);
    }

    notes_sz = PyList_Size(self->shared_notes);
    fwrite(&notes_sz, sizeof(int), 1, f);
    for (int i = 0; i < notes_sz; ++i) {
        obj = PyList_GetItem(self->shared_notes, i);
        obj_str = PyUnicode_AsUTF8(obj);
        obj_len = strlen(obj_str);
        fwrite(&obj_len, sizeof(int), 1, f);
        fwrite(obj_str, obj_len, 1, f);

        obj = PyList_GetItem(self->shared_notes_info, i);
        obj_str = PyUnicode_AsUTF8(obj);
        obj_len = strlen(obj_str);
        fwrite(&obj_len, sizeof(int), 1, f);
        fwrite(obj_str, obj_len, 1, f);
    }

    fclose(f);

    Py_XDECREF(self->username);
    Py_XDECREF(self->password);
    Py_XDECREF(self->secret_note);
    Py_XDECREF(self->key);
    Py_XDECREF(self->notes);
    Py_XDECREF(self->notes_info);
    Py_XDECREF(self->shared_notes);
    Py_XDECREF(self->shared_notes_info);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *User_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    UserObject *self;
    self = (UserObject *)type->tp_alloc(type, 0);
    if (self) {
        self->notes = PyList_New(0);
        if (self->notes == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->notes_info = PyList_New(0);
        if (self->notes_info == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->shared_notes = PyList_New(0);
        if (self->shared_notes == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->shared_notes_info = PyList_New(0);
        if (self->shared_notes_info == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->username = PyUnicode_FromString("");
        if (self->username == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->password = PyUnicode_FromString("");
        if (self->password == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->key = PyByteArray_FromStringAndSize("", 0);
        if (self->key == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->secret_note = PyByteArray_FromStringAndSize("", 0);
        if (self->secret_note == NULL) {
            Py_DECREF(self);
            return NULL;
        }
    }
    return (PyObject *)self;
}

static int User_init(UserObject *self, PyObject *args, PyObject *kwds) {
    PyObject *username_obj, *tmp;
    if (!PyArg_ParseTuple(args, "O", &username_obj)) return -1;

    if (username_obj) {
        tmp = self->username;
        Py_INCREF(username_obj);
        self->username = username_obj;
        Py_XDECREF(tmp);
    }

    char *username_str = PyUnicode_AsUTF8(username_obj);
    if (!username_str) return -1;

    char *path = get_path(username_str);
    FILE *f = fopen(path, "r");
    free(path);
    int pass_len = 0;
    char password[0x40] = {};
    fread(&pass_len, sizeof(int), 1, f);
    fread(password, pass_len, 1, f);
    self->password = Py_BuildValue("s", password, pass_len);
    if (!self->password) return -1;

    int secret_note_sz = 0;
    fread(&secret_note_sz, sizeof(int), 1, f);
    char *secret_note = calloc(1, secret_note_sz);
    fread(secret_note, secret_note_sz, 1, f);
    self->secret_note = PyByteArray_FromStringAndSize(secret_note, secret_note_sz);
    free(secret_note);

    int key_sz = 0;
    fread(&key_sz, sizeof(int), 1, f);
    char *key = calloc(1, key_sz);
    fread(key, key_sz, 1, f);
    self->key = PyByteArray_FromStringAndSize(key, key_sz);
    free(key);

    int notes_sz = 0;
    fread(&notes_sz, sizeof(int), 1, f);
    int buf_len = 0;
    char *buf;
    for (int i = 0; i < notes_sz; ++i) {
        fread(&buf_len, sizeof(int), 1, f);
        buf = calloc(1, buf_len);
        fread(buf, buf_len, 1, f);
        PyList_Append(self->notes, Py_BuildValue("s", buf, buf_len));
        free(buf);

        fread(&buf_len, sizeof(int), 1, f);
        buf = calloc(1, buf_len);
        fread(buf, buf_len, 1, f);
        PyList_Append(self->notes_info, Py_BuildValue("s", buf, buf_len));
        free(buf);
    }
    fread(&notes_sz, sizeof(int), 1, f);
    for (int i = 0; i < notes_sz; ++i) {
        fread(&buf_len, sizeof(int), 1, f);
        buf = calloc(1, buf_len);
        fread(buf, buf_len, 1, f);
        PyList_Append(self->shared_notes, Py_BuildValue("s", buf, buf_len));
        free(buf);

        fread(&buf_len, sizeof(int), 1, f);
        buf = calloc(1, buf_len);
        fread(buf, buf_len, 1, f);
        PyList_Append(self->shared_notes_info, Py_BuildValue("s", buf, buf_len));
        free(buf);
    }
    fclose(f);
    return 0;
}

static PyObject *User_add_secret_note(UserObject *self, PyObject *args) {
    PyObject *key, *secret_note, *tmp;
    if (!PyArg_ParseTuple(args, "OO", &secret_note, &key)) return NULL;
    if (secret_note) {
        tmp = self->secret_note;
        Py_INCREF(secret_note);
        self->secret_note = secret_note;
        Py_XDECREF(tmp);
    }
    if (key) {
        tmp = self->key;
        Py_INCREF(key);
        self->key = key;
        Py_XDECREF(tmp);
    }
    Py_RETURN_NONE;
}

static PyObject *User_show_secret_note(UserObject *self, PyObject *args) {
    char *secret_note, *key;
    int secret_note_len, key_len;
    secret_note_len = PyByteArray_Size(self->secret_note);
    secret_note = PyByteArray_AsString(self->secret_note);
    key_len = PyByteArray_Size(self->key);
    key = PyByteArray_AsString(self->key);
    if (!secret_note_len) return NULL;
    if (key_len != secret_note_len) return NULL;
    char *note = calloc(1, secret_note_len);
    for (int i = 0; i < secret_note_len; ++i) {
        note[i] = secret_note[i] ^ key[i];
    }
    return PyUnicode_FromStringAndSize(note, secret_note_len);
}

static PyObject *User_add_note(UserObject *self, PyObject *args) {
    if (PyList_Size(self->notes) > 10) return NULL;
    PyObject *note, *note_info;
    if (!PyArg_ParseTuple(args, "OO", &note, &note_info)) return NULL;
    if (PyList_Append(self->notes, note) < 0) return NULL;
    if (PyList_Append(self->notes_info, note_info) < 0) return NULL;
    Py_RETURN_NONE;
}

static PyObject *User_share_note(UserObject *self, PyObject *args) {
    int note_id;
    PyObject *note, *note_info;
    UserObject *user;
    if (!PyArg_ParseTuple(args, "iO", &note_id, &user)) return NULL;
    if (PyList_Size(user->shared_notes) > 10) return NULL;
    note = PyList_GetItem(self->notes, note_id);
    note_info = PyList_GetItem(self->notes_info, note_id);
    if (!note) return NULL;
    if (PyList_Append(user->shared_notes, note) < 0) return NULL;
    if (PyList_Append(user->shared_notes_info, note_info) < 0) return NULL;
    Py_RETURN_NONE;
}

static PyObject *User_get_note(UserObject *self, PyObject *args) {
    int note_id;
    PyObject *note, *note_info;
    if (!PyArg_ParseTuple(args, "i", &note_id)) return NULL;
    note = PyList_GetItem(self->notes, note_id);
    note_info = PyList_GetItem(self->notes_info, note_id);
    if (!note) return NULL;
    if (!note_info) return NULL;
    return Py_BuildValue("(OO)", note, note_info);
}

static PyObject *User_get_shared_note(UserObject *self, PyObject *args) {
    int note_id;
    PyObject *note, *note_info;
    if (!PyArg_ParseTuple(args, "i", &note_id)) return NULL;
    note = PyList_GetItem(self->shared_notes, note_id);
    note_info = PyList_GetItem(self->shared_notes_info, note_id);
    if (!note) return NULL;
    if (!note_info) return NULL;
    return Py_BuildValue("(OO)", note, note_info);
}

static PyObject *User_delete_note(UserObject *self, PyObject *args) {
    int index;
    if (!PyArg_ParseTuple(args, "i", &index)) return NULL;
    
    if (Py_SIZE(self->notes) == 0) return NULL;

    if (index < 0) index += Py_SIZE(self);

    if (index < 0 || index > Py_SIZE(self->notes)) return NULL;

    if (index < Py_SIZE(self->notes)-1) {
        if (PyList_SetSlice(self->notes, index, index+1, NULL) < 0) return NULL;
        if (PyList_SetSlice(self->notes_info, index, index+1, NULL) < 0) return NULL;
    }
    else {
        Py_XDECREF(((PyListObject*)self->notes)->ob_item[index]);
        Py_SIZE(self->notes) -= 1;
        Py_XDECREF(((PyListObject*)self->notes_info)->ob_item[index]);
        Py_SIZE(self->notes_info) -= 1;
    }
    Py_RETURN_NONE;
}

static PyObject *User_delete_shared_note(UserObject *self, PyObject *args) {
    int index;
    if (!PyArg_ParseTuple(args, "i", &index)) return NULL;
    
    if (Py_SIZE(self->shared_notes) == 0) return NULL;

    if (index < 0) index += Py_SIZE(self);

    if (index < 0 || index > Py_SIZE(self->shared_notes)) return NULL;

    if (index < Py_SIZE(self->shared_notes)-1) {
        if (PyList_SetSlice(self->shared_notes, index, index+1, NULL) < 0) return NULL;
        if (PyList_SetSlice(self->shared_notes_info, index, index+1, NULL) < 0) return NULL;
    }
    else {
        Py_XDECREF(((PyListObject*)self->shared_notes)->ob_item[index]);
        Py_SIZE(self->shared_notes) -= 1;
        Py_XDECREF(((PyListObject*)self->shared_notes_info)->ob_item[index]);
        Py_SIZE(self->shared_notes_info) -= 1;
    }
    Py_RETURN_NONE;
}

static PyMemberDef User_members[] = {
    {"username", T_OBJECT_EX, offsetof(UserObject, username), 0, "username"},
    {"password", T_OBJECT_EX, offsetof(UserObject, password), 0, "password"},
    {"secret_note", T_OBJECT_EX, offsetof(UserObject, secret_note), 0, "secret_note"},
    {"key", T_OBJECT_EX, offsetof(UserObject, key), 0, "key"},
    {"notes", T_OBJECT_EX, offsetof(UserObject, notes), 0, "notes"},
    {"notes_info", T_OBJECT_EX, offsetof(UserObject, notes_info), 0, "notes_info"},
    {"shared_notes", T_OBJECT_EX, offsetof(UserObject, shared_notes), 0, "shared_notes"},
    {"shared_notes_info", T_OBJECT_EX, offsetof(UserObject, shared_notes_info), 0, "shared_notes_info"},
    {NULL},
};

static PyMethodDef User_methods[] = {
    {"add_note", (PyCFunction)User_add_note, METH_VARARGS, "add_note"},
    {"add_secret_note", (PyCFunction)User_add_secret_note, METH_VARARGS, "add_secret_note"},
    {"show_secret_note", (PyCFunction)User_show_secret_note, METH_VARARGS, "show_secret_note"},
    {"get_note", (PyCFunction)User_get_note, METH_VARARGS, "get_note"},
    {"delete_note", (PyCFunction)User_delete_note, METH_VARARGS, "delete_note"},
    {"get_shared_note", (PyCFunction)User_get_shared_note, METH_VARARGS, "get_shared_note"},
    {"delete_shared_note", (PyCFunction)User_delete_shared_note, METH_VARARGS, "delete_shared_note"},
    {"share_note", (PyCFunction)User_share_note, METH_VARARGS, "share_note"},
    {NULL}
};

static PyTypeObject UserType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "userlib.User",
    .tp_doc = PyDoc_STR(""),
    .tp_basicsize = sizeof(UserObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = User_new,
    .tp_init = (initproc) User_init,
    .tp_dealloc = (destructor) User_dealloc,
    .tp_members = User_members,
    .tp_methods = User_methods,
};

PyMethodDef userlib_methods[] = {
    {"validate_creds", userlib_validate_creds, METH_VARARGS, "Validate creds"},
    {"is_valid_string", userlib_is_valid_string, METH_VARARGS, "Check that string is valid for credentials"},
    {"user_exists", userlib_user_exists, METH_VARARGS, "Check that user exists"},
    {"check_password", userlib_check_password, METH_VARARGS, "Check that password is correct"},
    {"store_new_user", userlib_store_new_user, METH_VARARGS, "Add new user to storage"},
    {NULL, NULL, 0, NULL}
};

struct PyModuleDef userlib_module = {
    PyModuleDef_HEAD_INIT,
    "userlib",
    "",
    -1,
    userlib_methods
};

PyObject *PyInit_userlib(void) {
    PyObject *m;
    if (PyType_Ready(&UserType) < 0) return 0;

    m = PyModule_Create(&userlib_module);
    if (m == NULL) return 0;

    Py_INCREF(&UserType);
    if (PyModule_AddObject(m, "User", (PyObject*)&UserType) < 0) {
        Py_DECREF(&UserType);
        Py_DECREF(m);
        return 0;
    }
    return m;
}
