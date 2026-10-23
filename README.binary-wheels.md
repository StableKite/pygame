# Experimental CPython 3.15t Linux wheels

A normal `pip install` from this repository selects the verified release wheel
for the recorded source snapshot on Linux x86_64, CPython 3.15t and glibc 2.39+.
pip performs downloading, dependency resolution and SHA256 validation.
No consumer SDK setup or extra build flag is required for this binary path.

The original PEP 517 backend and its build requirements are preserved. Changed
native/build sources, another ABI/platform, explicit configuration settings or
compiler overrides use that original source build. The JSON manifest records
the source commit, artifact hash and the checked delivery metadata. Source
builds retain their ordinary development-library prerequisites.

These are engineering dependency artifacts, not a StableKite release.

The native pygame implementation still requires `PYTHON_GIL=0` or `-X gil=0`
to keep the GIL disabled. This adapter does not mark unsafe modules as nogil-safe.
The tested dummy SDL suite passes 1842 tests in that runtime mode.
