"""Run the shared conformance suite against S3Adapter.

The wildcard import is intentional: it pulls every ``test_*`` function from
``files_sdk.testing.conformance`` into this module so pytest discovers them and
binds them to the local ``adapter`` fixture defined in conftest.py.
"""

from files_sdk.testing.conformance import *  # noqa: F401,F403
