#! /usr/bin/env python

"""Unit test base class and utils"""

from mock import Mock, mocksignature, patch, DEFAULT
import unittest

from zope.interface import implementedBy
from pyon.service.service import get_service_by_name
from pyon.core.object import IonServiceRegistry

test_obj_registry = IonServiceRegistry()
test_obj_registry.register_obj_dir('obj/data')
test_obj_registry.register_svc_dir('obj/services')

def func_names(cls):
    import types
    return [name for name, value in cls.__dict__.items() if
            isinstance(value, types.FunctionType)]

def pop_last_call(mock):
    if not mock.call_count:
        raise AssertionError('Cannot pop last call: call_count is 0')
    mock.call_args_list.pop()
    try:
        mock.call_args = mock.call_args_list[-1]
    except IndexError:
        mock.call_args = None
        mock.called = False
    mock.call_count -= 1

class PyonTestCase(unittest.TestCase):
    # Call this function at the beginning of setUp if you need a mock ion
    # obj
    def _create_object_mock(self, name):
        mock_ionobj = Mock(name='IonObject')
        def side_effect(_def, _dict=None, **kwargs):
            test_obj = test_obj_registry.new(_def, _dict, **kwargs)
            test_obj._validate()
            return DEFAULT
        mock_ionobj.side_effect = side_effect
        patcher = patch(name, mock_ionobj)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def _create_service_mock(self, service_name):
        # set self.clients if not already set
        if getattr(self, 'clients', None) is None:
            setattr(self, 'clients', Mock(name='self.clients'))
        base_service = get_service_by_name(service_name)
        # Save it to use in test_verify_service
        self.base_service = base_service
        dependencies = base_service.dependencies
        for dep_name in dependencies:
            dep_service = get_service_by_name(dep_name)
            # Force mock service to use interface
            mock_service = Mock(name='self.clients.%s' % dep_name,
                    spec=dep_service)
            setattr(self.clients, dep_name, mock_service)
            # set self.dep_name for conevenience
            setattr(self, dep_name, mock_service)
            iface = list(implementedBy(dep_service))[0]
            names_and_methods = iface.namesAndDescriptions()
            for func_name, _ in names_and_methods:
                mock_func = mocksignature(getattr(dep_service, func_name),
                        mock=Mock(name='self.clients.%s.%s' % (dep_name,
                            func_name)), skipfirst=True)
                setattr(mock_service, func_name, mock_func)

    # Assuming your service is the only subclass of the Base Service
    def test_verify_service(self):
        if not getattr(self, 'base_service', None):
            raise unittest.SkipTest('Not implementing an Ion Service')
        from zope.interface.verify import verifyClass
        base_service = self.base_service
        implemented_service = base_service.__subclasses__()[0]
        iface = list(implementedBy(base_service))[0]
        verifyClass(iface, implemented_service)
        # Check if defined functions in Base Service are all implemented
        difference = set(func_names(base_service)) - set(func_names(implemented_service)) - set(['__init__'])
        if difference:
            self.fail('Following function declarations in %s do not exist in %s : %s' %
                    (iface, implemented_service,
                        list(difference)))