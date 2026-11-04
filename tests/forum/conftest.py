"""Đóng mọi engine sau mỗi test: role trên Supabase/#193 có CONNECTION LIMIT 20.

Engine vẫn dùng lại được sau dispose (tự mở kết nối mới), nên fixture dùng chung không bị ảnh hưởng.
"""
import pytest

from services.forum import app as forum_app

_created: list = []
_orig_init = forum_app.Stores.__init__


def _tracking_init(self, *a, **kw):
    _orig_init(self, *a, **kw)
    _created.append(self)


forum_app.Stores.__init__ = _tracking_init


@pytest.fixture(autouse=True)
def _dispose_engines():
    yield
    for st in _created:
        st.dispose()
