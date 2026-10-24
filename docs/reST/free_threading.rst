Free-threaded CPython
=====================

On a free-threaded CPython build, importing pygame and its native modules
leaves the GIL disabled without PYTHON_GIL or -X gil runtime overrides.
The handwritten extension modules use strong references for values read from
public dictionaries, immutable snapshots across sequence conversions, and
explicit synchronization for SDL timer records and mixer callback ownership.
The Cython modules are generated with Cython 3.3 or newer.

This does not change SDL's thread-affinity requirements. Initialize, configure
and shut down display/audio subsystems in one owning thread. Display and
window operations remain on SDL's main thread. Serialize music controls and
subsystem lifecycle calls. An individual Surface, Rect, Color, Vector, Font,
Camera, PixelArray, Sprite or Group must not be mutated concurrently without
an application lock. Sharing raw surface/audio buffers requires the same
synchronization as direct NumPy/buffer writes. Separate objects may be used
concurrently subject to the underlying SDL API's threading restrictions.
These are object/subsystem ownership rules, not a global interpreter lock.

``pygame.tests.free_threaded_test`` exercises default imports, reentrant and
concurrent input mutation, SDL timer cancellation and audio callback ownership.
