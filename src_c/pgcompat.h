/* Python 2.x/3.x compatibility tools (internal)
 */
#ifndef PGCOMPAT_INTERNAL_H
#define PGCOMPAT_INTERNAL_H

#include "include/pgcompat.h"

/* Module init function returns new module instance. */
#define MODINIT_DEFINE(mod_name) PyMODINIT_FUNC PyInit_##mod_name(void)

/* Defaults for unicode file path encoding */
#if defined(MS_WIN32)
#define UNICODE_DEF_FS_ERROR "replace"
#else
#define UNICODE_DEF_FS_ERROR "surrogateescape"
#endif

#define RELATIVE_MODULE(m) ("." m)

#ifndef Py_TPFLAGS_HAVE_NEWBUFFER
#define Py_TPFLAGS_HAVE_NEWBUFFER 0
#endif

#define Slice_GET_INDICES_EX(slice, length, start, stop, step, slicelength) \
    PySlice_GetIndicesEx(slice, length, start, stop, step, slicelength)

/* Return a strong reference; borrowed weakref access was removed in 3.15. */
static inline int
pgWeakref_GetRef(PyObject *ref, PyObject **pobj)
{
#if PY_VERSION_HEX >= 0x030d0000
    return PyWeakref_GetRef(ref, pobj);
#else
    PyObject *obj = PyWeakref_GetObject(ref);
    *pobj = NULL;
    if (obj == NULL) {
        return -1;
    }
    if (obj == Py_None) {
        return 0;
    }
    Py_INCREF(obj);
    *pobj = obj;
    return 1;
#endif
}


/* Borrowed dict values can disappear while another Python thread mutates the
 * dictionary. Keep a strong reference across conversions and user callbacks. */
static inline PyObject *
pgDict_GetItemRef(PyObject *dict, PyObject *key)
{
#if PY_VERSION_HEX >= 0x030d0000
    PyObject *result = NULL;
    PyDict_GetItemRef(dict, key, &result);
    return result;
#else
    PyObject *result = PyDict_GetItemWithError(dict, key);
    Py_XINCREF(result);
    return result;
#endif
}

static inline PyObject *
pgDict_GetItemStringRef(PyObject *dict, const char *key)
{
#if PY_VERSION_HEX >= 0x030d0000
    PyObject *result = NULL;
    PyDict_GetItemStringRef(dict, key, &result);
    return result;
#else
    PyObject *name = PyUnicode_FromString(key), *result;
    if (!name) return NULL;
    result = pgDict_GetItemRef(dict, name);
    Py_DECREF(name);
    return result;
#endif
}


/* CPython's default import must preserve free threading. The runtime paths
 * using borrowed mutable-container values, SDL timer records and channel
 * callback references use owned snapshots/locks (see free_threaded_test.py).
 * SDL's main-thread/lifecycle rules and Sprite/Group external synchronization
 * requirements continue to apply; no process-wide replacement GIL is used. */
static inline PyObject *
pgModule_Create(struct PyModuleDef *definition)
{
    PyObject *module = PyModule_Create(definition);
#ifdef Py_GIL_DISABLED
    if (module) PyUnstable_Module_SetGIL(module, Py_MOD_GIL_NOT_USED);
#endif
    return module;
}

#endif /* ~PGCOMPAT_INTERNAL_H */

/* Critical sections are no-ops on older GIL-only CPython releases. */
#ifndef Py_BEGIN_CRITICAL_SECTION
#define Py_BEGIN_CRITICAL_SECTION(op) {
#define Py_END_CRITICAL_SECTION() }
#endif
