"""Build the pinned SDL2 Windows timer fix without changing timer policy."""

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import urllib.request


SOURCE_COMMIT = 'cc016b0046d563287f0aa9f09b958b5e70d43696'
SOURCE_SHA256 = '2f7e3901167aceb34741b3b62e3200b422ed7418f7ee97a416c097ac31a56b5f'
SOURCE_URL = 'https://codeload.github.com/libsdl-org/SDL/tar.gz/' + SOURCE_COMMIT
VENDOR = 'StableKite SDL2 2.28.4 precise Windows delay v1'


def ensure_precise_delay(prebuilt_dir, machine_type):
    """Replace only the bundled SDL2 with a normal build of the checked patch."""
    if machine_type not in ('x64', 'x86'):
        raise RuntimeError('Unsupported SDL2 build architecture: ' + machine_type)
    patch = Path(__file__).with_name('stablekite-sdl2-precise-delay.patch')
    cmake = shutil.which('cmake')
    if cmake is None:
        raise RuntimeError('CMake 4.2 or newer is required to build bundled SDL2')
    cmake_version = subprocess.check_output([cmake, '--version'], text=True)
    inputs = {
        'source_commit': SOURCE_COMMIT,
        'source_sha256': SOURCE_SHA256,
        'patch_sha256': sha256(patch.read_bytes()).hexdigest(),
        'vendor': VENDOR,
        'machine': machine_type,
        'cmake': cmake,
        'cmake_version': cmake_version,
        'compiler_environment': {
            name: os.environ.get(name)
            for name in (
                'CC', 'CXX', 'CFLAGS', 'CXXFLAGS', 'LDFLAGS',
                'CMAKE_GENERATOR', 'CMAKE_GENERATOR_PLATFORM',
                'CMAKE_GENERATOR_TOOLSET', 'VSINSTALLDIR',
                'VCToolsInstallDir', 'WindowsSDKVersion',
            )
        },
    }
    key = sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    cache = Path('prebuilt_downloads') / 'stablekite-sdl2-precise-delay-v1' / key
    cache.mkdir(parents=True, exist_ok=True)
    receipt = cache / 'BUILD.json'
    dll = cache / 'build' / 'Release' / 'SDL2.dll'
    if receipt.is_file():
        record = json.loads(receipt.read_text(encoding='utf8'))
        if record['inputs'] != inputs or record['dll_sha256'] != sha256(dll.read_bytes()).hexdigest():
            raise RuntimeError('Cached SDL2 build does not match its recorded inputs')
    else:
        archive = cache / 'SDL2-source.tar.gz'
        if not archive.is_file():
            with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
                archive.write_bytes(response.read())
        if sha256(archive.read_bytes()).hexdigest() != SOURCE_SHA256:
            raise RuntimeError('Pinned SDL2 source archive hash mismatch')
        source = cache / 'source'
        source.mkdir(exist_ok=False)
        with tarfile.open(archive) as contents:
            prefix = 'SDL-' + SOURCE_COMMIT
            for entry in contents.getmembers():
                name = PurePosixPath(entry.name)
                if name.parts[0] != prefix or '..' in name.parts or '\\' in entry.name or ':' in entry.name:
                    raise RuntimeError('Unsafe SDL2 archive path')
                relative = PurePosixPath(*name.parts[1:])
                target = source.joinpath(*relative.parts)
                if target.resolve() != source.resolve() and source.resolve() not in target.resolve().parents:
                    raise RuntimeError('SDL2 archive path escapes source directory')
                if entry.issym() and str(relative) in ('android-project-ant/AndroidManifest.xml', 'android-project-ant/src'):
                    # Android project links are unused by the Windows build.
                    continue
                if entry.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif entry.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with contents.extractfile(entry) as stream:
                        target.write_bytes(stream.read())
                else:
                    raise RuntimeError('Unsupported SDL2 archive entry')
        subprocess.check_call(['git', 'init', '--quiet', str(source)])
        subprocess.check_call(['git', 'apply', '--unidiff-zero', '--check', str(patch.resolve())], cwd=source)
        subprocess.check_call(['git', 'apply', '--unidiff-zero', str(patch.resolve())], cwd=source)
        args = [cmake, '-S', str(source.resolve()), '-B', str((cache / 'build').resolve())]
        generator = os.environ.get('CMAKE_GENERATOR', '')
        if not generator or generator.startswith('Visual Studio'):
            args.extend(['-A', 'x64' if machine_type == 'x64' else 'Win32'])
        args.extend([
            '-DSDL_SHARED=ON', '-DSDL_STATIC=OFF', '-DSDL_TEST=OFF',
            '-DSDL_TESTS=OFF', '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
            '-DSDL_VENDOR_INFO=' + VENDOR,
            '-DCMAKE_BUILD_TYPE=Release',
        ])
        subprocess.check_call(args)
        subprocess.check_call([cmake, '--build', str(cache / 'build'), '--config', 'Release', '--parallel', '4'])
        if not dll.is_file():
            # Single-configuration generators place the same target here.
            single = cache / 'build' / 'SDL2.dll'
            if not single.is_file():
                raise RuntimeError('SDL2 build did not produce its shared library')
            dll.parent.mkdir(exist_ok=True)
            shutil.copyfile(single, dll)
        receipt.write_text(json.dumps({'inputs': inputs, 'dll_sha256': sha256(dll.read_bytes()).hexdigest()}, indent=2) + '\n', encoding='utf8')
    target = Path(prebuilt_dir) / 'SDL2-2.28.4' / 'lib' / machine_type / 'SDL2.dll'
    if not target.is_file():
        raise RuntimeError('Expected bundled SDL2 dependency was not found')
    shutil.copyfile(dll, target)
