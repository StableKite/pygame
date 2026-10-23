import concurrent.futures
import sys
import sysconfig
import unittest
import pygame


@unittest.skipUnless(sysconfig.get_config_var("Py_GIL_DISABLED")
                     and not sys._is_gil_enabled(),
                     "requires free-threaded Python with GIL disabled")
class SurfaceLockConcurrencyTest(unittest.TestCase):
    def test_shared_lock_bookkeeping(self):
        surface = pygame.Surface((8, 8))
        surface.lock()
        surface.unlock()
        def mutate():
            for _ in range(10000):
                surface.lock()
                surface.unlock()
        def observe():
            for _ in range(10000):
                self.assertTrue(all(obj is surface for obj in surface.get_locks()))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs = [pool.submit(mutate) for _ in range(2)]
            jobs += [pool.submit(observe) for _ in range(2)]
            for job in jobs:
                job.result(timeout=15)
        self.assertFalse(surface.get_locked())
        self.assertEqual(surface.get_locks(), ())
