# Precise native Windows audio timing

The bundled Windows SDL2 is built from the original SDL 2.28.4 source at
`cc016b0046d563287f0aa9f09b958b5e70d43696`, with the checked local patch
`buildconfig/stablekite-sdl2-precise-delay.patch`. Its revision records
`StableKite SDL2 2.28.4 precise Windows delay v1`. The source archive is pinned
by SHA256 in `buildconfig/stablekite_sdl2.py`; the normal CMake build records
its exact inputs and resulting DLL hash. Other bundled dependency files stay
unchanged. Source builds need CMake and a native Windows compiler.

Windows may ignore timer-resolution requests for background processes:
https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod
On the affected host, the original SDL_Delay(11) changes from about 11.5 ms
to about 15.5 ms after three seconds even without any pygame test. The disk
audio driver uses this wait for each buffer and consequently plays too slowly.

The patch uses a native high-resolution waitable timer for nonzero delays,
closes each handle, and retains the original Sleep fallback on older Windows
or an API failure. It preserves zero-delay yielding, does not change timer
policy, and does not shorten requested waits:
https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createwaitabletimerexw

The original test backend, waits, assertions, workers, and timeouts are kept.
The separate test reporting fix retains ordinary FAIL tracebacks and prevents
a failure summary from being printed as OK.

Native prototype measurements are complete. Full wheel and original suite
qualification for this source version must complete before default delivery.
