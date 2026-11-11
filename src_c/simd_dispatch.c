/* Runtime dispatch must use the baseline target, even when AVX2 blitters are
 * built. Never enter an AVX2-targeted object on a CPU without AVX2 support. */
#include "simd_blitters.h"

int
pg_has_avx2()
{
    return SDL_HasAVX2() && pg_avx2_compiled();
}

int
pg_avx2_at_runtime_but_uncompiled()
{
    return SDL_HasAVX2() && !pg_avx2_compiled();
}
