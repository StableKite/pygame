# Qualified CPython 3.15t Windows and Linux wheels

Normal `pip install git+https://github.com/StableKite/pygame.git` selects the
checked release wheel for the exact source snapshot on CPython 3.15t, Windows
AMD64 or Linux x86_64 with glibc 2.27 or newer. pip verifies the pinned SHA256.
The installed genuine version is `2.6.1+stablekite.6`; no runtime GIL override
or consumer overlay is used.

AVX2 is compiled only for the dedicated blitters and selected by actual CPU
dispatch. The same Linux wheel passed 200 exact blend comparisons under native
AVX2 and QEMU Nehalem without AVX2. The full original command passed 1852 tests
on each actual CPython 3.15.2t OS with the original disk audio backend, waits,
assertions, exclusions and 300-second per-module timeout.

Windows SDL2 is reproducibly built from the pinned original 2.28.4 source with
the precise native wait patch described in `STABLEKITE_SDL2.md`. Its revision
marks the local change. Other bundled media dependencies retain their inputs.

Changed source, another platform or ABI, explicit configuration settings,
compiler overrides, or any explicit `PYGAME_DETECT_AVX2` value (including an
empty value) select the original source build. A deliberate AVX2 optout keeps
the original missing-AVX2 warning and baseline fallback; negative control
wheels are kept private and are never release assets.

The manifest records the immutable runtime source, checked carrier files and
separate platform artifacts. Source builds retain their normal native compiler
and development-library requirements; bundled Windows source builds also need
CMake. These are engineering dependency artifacts in the StableKite fork.

Repository attributes keep the checked delivery files and SDL patch in their
canonical LF form, including ordinary Windows Git checkouts with automatic
line-ending conversion. Hash validation remains byte-exact.
