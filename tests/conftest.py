from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_ctrlvars():
    """Patch ``epics.PV.get_ctrlvars`` so devices build without a live IOC.

    Tests set ``return_value`` to the ctrl options they need.
    """
    with patch("epics.PV.get_ctrlvars", new_callable=MagicMock) as mock:
        yield mock
