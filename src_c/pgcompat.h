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

#endif /* ~PGCOMPAT_INTERNAL_H */
