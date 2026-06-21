"""Root conftest.

Its mere presence puts the project root on ``sys.path`` (pytest prepend mode),
so tests can ``import agents`` / ``import integrator`` regardless of where
pytest is invoked from.
"""
