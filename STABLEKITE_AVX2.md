This 2.6.1+stablekite.1 review enables the existing per-object AVX2 build by
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
