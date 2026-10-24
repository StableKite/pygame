"""Regression coverage for native ownership with CPython's default GIL OFF."""
import concurrent.futures
import importlib
import math
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import threading
import time
import unittest

import pygame


@unittest.skipUnless(sysconfig.get_config_var('Py_GIL_DISABLED'), 'free-threaded CPython required')
class FreeThreadedTest(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_default_imports_preserve_disabled_gil(self):
        env = os.environ.copy()
        env.pop('PYTHON_GIL', None)
        root = Path(pygame.__file__).parent
        modules = sorted('pygame.' + str(p.relative_to(root)).replace(os.sep, '.').split('.cpython-')[0]
                         for p in root.rglob('*.so') if '.cpython-' in p.name)
        code = ('import importlib,sys; assert "gil" not in sys._xoptions; '
                'assert not sys._is_gil_enabled(); '
                '[(importlib.import_module(m), '
                '(_ for _ in ()).throw(AssertionError(m)) if sys._is_gil_enabled() else None) '
                'for m in ' + repr(modules) + ']; print(len(' + repr(modules) + '))')
        result = subprocess.run([sys.executable, '-c', code], env=env, cwd='/tmp',
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertGreaterEqual(int(result.stdout.strip().splitlines()[-1]), 30)
        self.assertFalse(sys._is_gil_enabled())

    def test_vector_conversion_pins_mutable_input(self):
        source = []
        class Number:
            def __init__(self, value): self.value = value
            def __float__(self):
                source.clear()
                return self.value
        source.extend([Number(3.0), Number(4.0)])
        self.assertEqual(pygame.Vector2().distance_to(source), 5.0)
        self.assertEqual(source, [])

    def test_concurrent_custom_types_are_unique(self):
        barrier = threading.Barrier(8)
        def worker(index):
            barrier.wait()
            return [pygame.event.custom_type() for _ in range(100)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            values = [n for row in pool.map(worker, range(8)) for n in row]
        self.assertEqual(len(set(values)), 800)

    def test_concurrent_quit_registration_retains_every_callback(self):
        called = []
        barrier = threading.Barrier(4)
        def worker(index):
            barrier.wait()
            for i in range(100):
                pygame.register_quit(lambda value=(index, i): called.append(value))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(worker, range(4)))
        pygame.quit()
        self.assertEqual(len(called), 400)
        self.assertEqual(len(set(called)), 400)

    def test_event_reinitialization_releases_previous_dict(self):
        import gc
        import weakref
        class Payload: pass
        obj = Payload()
        ref = weakref.ref(obj)
        event = pygame.event.Event(pygame.USEREVENT, payload=obj)
        del obj
        event.__init__(pygame.USEREVENT, replacement=True)
        gc.collect()
        self.assertIsNone(ref())
        self.assertTrue(event.replacement)

    def test_collision_snapshot_survives_reentrant_dict_clear(self):
        for method, expected in [('collidedict', ('hit', (0, 0, 1, 1))),
                                 ('collidedictall', [('hit', (0, 0, 1, 1))])]:
            source = {}
            class RectLike:
                @property
                def rect(self):
                    source.clear()
                    return pygame.Rect(100, 100, 1, 1)
            source.update(miss=RectLike(), hit=(0, 0, 1, 1))
            result = getattr(pygame.Rect(0, 0, 8, 8), method)(source, values=True)
            self.assertEqual(result, expected)
            self.assertEqual(source, {})

    def test_concurrent_named_color_ownership(self):
        from pygame.colordict import THECOLORS
        key = 'stablekitefreethreadtest'
        barrier = threading.Barrier(4)
        def worker(index):
            barrier.wait()
            for i in range(4000):
                if index == 0:
                    THECOLORS[key] = tuple([i % 256, 20, 30, 255])
                else:
                    self.assertEqual(pygame.Color(key).a, 255)
        THECOLORS[key] = (1, 20, 30, 255)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(worker, range(4)))
        finally:
            THECOLORS.pop(key, None)

    def test_concurrent_timer_replace_cancel_and_expiry(self):
        pygame.display.init()
        pygame.display.set_mode((8, 8))
        types = [pygame.event.custom_type() for _ in range(4)]
        def worker(kind):
            for i in range(200):
                event = pygame.event.Event(kind, payload=bytearray([i % 256] * 64))
                pygame.time.set_timer(event, 1, loops=1)
                if i % 4:
                    time.sleep(0.0005)
                pygame.time.set_timer(kind, 0)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(worker, types))
        time.sleep(0.005)
        for event in pygame.event.get(types):
            self.assertIsInstance(event.payload, bytearray)
            self.assertEqual(len(event.payload), 64)
        self.assertFalse(sys._is_gil_enabled())

    def test_mixer_callback_owns_sound_and_queue_during_resize(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=128)
        pygame.mixer.set_num_channels(8)
        barrier = threading.Barrier(5)
        def worker(index):
            channel = pygame.mixer.Channel(index)
            barrier.wait()
            for i in range(800):
                sound = pygame.mixer.Sound(buffer=b'\0' * 256)
                queued = pygame.mixer.Sound(buffer=b'\0' * 128)
                channel.play(sound)
                channel.queue(queued)
                current = channel.get_sound()
                pending = channel.get_queue()
                self.assertTrue(current is None or isinstance(current, pygame.mixer.Sound))
                self.assertTrue(pending is None or isinstance(pending, pygame.mixer.Sound))
                channel.set_endevent(0)
                if i % 3 == 0: channel.stop()
            channel.stop()
        def resize():
            barrier.wait()
            for i in range(800): pygame.mixer.set_num_channels(8 + (i % 16))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(worker, i) for i in range(4)] + [pool.submit(resize)]
            for future in futures: future.result(timeout=60)
        self.assertFalse(sys._is_gil_enabled())

    def test_removed_channel_rejects_python_state_access(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        channel = pygame.mixer.Channel(15)
        sound = pygame.mixer.Sound(buffer=b'\0' * 256)
        pygame.mixer.set_num_channels(4)
        for method, args in [(channel.play, (sound,)), (channel.queue, (sound,)),
                             (channel.get_sound, ()), (channel.get_queue, ()),
                             (channel.get_endevent, ()), (channel.set_endevent, (0,)),
                             (channel.stop, ())]:
            with self.assertRaises(pygame.error): method(*args)


if __name__ == '__main__':
    unittest.main()
