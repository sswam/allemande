import io
import time
import pytest
from unittest.mock import patch, MagicMock
from types import ModuleType

import lazy as subject

__version__ = "0.1.3"

def test_lazy_returns_quickly():
    start_time = time.time()
    result = subject.lazy('xml.etree.ElementTree')
    end_time = time.time()

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], subject.LazyProxy)
    assert end_time - start_time < 0.1  # Ensure it returns in less than 0.1 seconds

def test_lazy_load_does_not_mess_with_namespace():
    global xml
    xml = None
    result = subject.lazy_load('xml')
    assert xml is None

def test_lazy_messes_with_namespace():
    global xml
    xml = None
    result = subject.lazy('xml')
    assert xml == result[0]
    assert xml.__name__ == 'xml'

def test_lazy_module_type():
    proxy = subject.lazy('xml.etree.ElementTree')[0]
    assert isinstance(proxy, subject.LazyProxy)

    loaded_module = proxy._LazyProxy_load()
    assert isinstance(loaded_module, ModuleType)

def test_lazy_symbol_type():
    proxy = subject.lazy('xml.etree.ElementTree', 'Element')[1]
    assert isinstance(proxy, subject.LazyProxy)

    Element = proxy._LazyProxy_load()
    assert callable(Element)

def test_lazy_as():
    proxy = subject.lazy('xml.etree.ElementTree', _as='ET')[0]
    assert isinstance(proxy, subject.LazyProxy)

    ET = proxy._LazyProxy_load()
    assert isinstance(ET, ModuleType)
    assert ET.__name__ == 'xml.etree.ElementTree'

def test_lazy_lambda():
    proxy = subject.lazy('xml.etree.ElementTree', custom_element=lambda ET: ET.Element('root'))[1]
    assert isinstance(proxy, subject.LazyProxy)

    custom_element = proxy._LazyProxy_load()
    assert custom_element.tag == 'root'

@patch('importlib.import_module')
def test_lazy_load_all_modules(mock_import_module):
    mock_module = MagicMock()
    mock_import_module.return_value = mock_module

    subject.maybe_unloaded_proxies = []

    subject.lazy('xml.etree.ElementTree')
    subject.lazy('xml.dom')

    assert len(subject.maybe_unloaded_proxies) == 1

    subject.load_all_modules()

    assert len(subject.maybe_unloaded_proxies) == 0
    assert mock_import_module.call_count == 1

def test_lazy_load():
    result = subject.lazy_load('xml.etree.ElementTree', 'Element')
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(proxy, subject.LazyProxy) for proxy in result)

if __name__ == '__main__':
    pytest.main([__file__])
