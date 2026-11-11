This 2.6.1+stablekite.4 review enables the existing per-object AVX2 build by
default on supported x86 targets. Only simd_blitters_avx2 receives -mavx2 or
/arch:AVX2. Other native units retain their baseline compiler target. An
explicit empty PYGAME_DETECT_AVX2 still requests the original disabled build.

SDL CPU detection and dispatch now live in a separate baseline C unit. A CPU
without AVX2 short-circuits before any code in the AVX2 object is entered.
The existing SSE2/scalar paths, blending operations and their tests remain.
The existing warning remains active for an explicitly disabled build on an
AVX2-capable machine; no warning filter or fake feature report is used.

The older binary-wheel manifest remains an honest record of the older source
and artifact. Changed build/native sources reject that binary shortcut and
use the original source backend until a new binary is separately qualified.
No existing release asset or published version is replaced by this review.

The compiler hook supports the modern setuptools Compiler.call API and the
legacy Compiler.spawn API. It forwards the original environment, dry-run and
error handling through the original method. AVX2 options are applied only to
the blitter compilation command, never link commands or the baseline dispatcher.
The previous private build exposed that setuptools 84 no longer calls spawn;
its native negative result and warning are retained outside this source tree.

The third private review fixes verified Windows packaging/discovery issues:
the bundled TIFF dependency is loaded by absolute path, the DLL-directory
handle remains owned by the package, and missing registry font files are not
advertised as usable fonts. The existing free-threaded import test uses the
actual platform extension suffixes and temporary directory on both systems.
All its GIL and module-count assertions remain. The verbose test aggregator
accepts a pending description before actual failed subtest result lines, while
retaining those failures and rejecting other unrecognized result states.

The fourth review follows the repository's original pinned format tools.
Native C tokens and every original test assertion are preserved. The MSVC
helper imports the same compiler factory through setuptools' modern module.
An explicit AVX2 build option always requests a source build, including an
empty option requesting disabled support; no binary shortcut overrides it.
