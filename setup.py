from setuptools import setup

try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    BuildDoc = None

setup(
    setup_requires=['pbr'],
    pbr=True,
    cmdclass={'build_sphinx': BuildDoc},
)
