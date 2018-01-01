import mock
import unittest

import cxxd_mocks
import service

class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.payload = [0x1, 0x2, 0x3]
        self.service = service.Service(cxxd_mocks.ServicePluginMock())

    def test_if_listening_is_enabled_by_default(self):
        self.assertEqual(self.service.keep_listening, True)

    def test_if_send_startup_request_enqueues_correct_data(self):
        with mock.patch.object(self.service.queue, 'put') as mock_queue_put:
            self.service.send_startup_request(self.payload)
        mock_queue_put.assert_called_with([0x0, self.payload])

    def test_if_send_shutdown_request_enqueues_correct_data(self):
        with mock.patch.object(self.service.queue, 'put') as mock_queue_put:
            self.service.send_shutdown_request(self.payload)
        mock_queue_put.assert_called_with([0x1, self.payload])

    def test_if_send_request_enqueues_correct_data(self):
        with mock.patch.object(self.service.queue, 'put') as mock_queue_put:
            self.service.send_request(self.payload)
        mock_queue_put.assert_called_with([0x2, self.payload])

    def test_if_send_startup_request_triggers_service_startup_callback(self):
        self.service.send_startup_request(self.payload)
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, 'startup_callback') as mock_startup_callback:
            self.service.listen()
        mock_startup_callback.assert_called_with(self.payload)

    def test_if_send_startup_request_triggers_service_plugin_startup_callback(self):
        self.service.send_startup_request(self.payload)
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service.service_plugin, 'startup_callback') as mock_startup_callback:
            self.service.listen()
        mock_startup_callback.assert_called_with(True, self.payload)

    def test_if_send_startup_request_triggers_service_startup_request_first_and_service_plugin_startup_request_second(self):
        manager = mock.MagicMock()
        self.service.send_startup_request(self.payload)
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, 'startup_callback') as mock_service_startup_callback:
            with mock.patch.object(self.service.service_plugin, 'startup_callback') as mock_service_plugin_startup_callback:
                manager.attach_mock(mock_service_startup_callback, 'mock_service_startup_callback')
                manager.attach_mock(mock_service_plugin_startup_callback, 'mock_service_plugin_startup_callback')
                self.service.listen()
        mock_service_startup_callback.assert_called_with(self.payload)
        mock_service_plugin_startup_callback.assert_called_with(True, self.payload)
        manager.assert_has_calls(
            [mock.call.mock_service_startup_callback(self.payload), mock.call.mock_service_plugin_startup_callback(True, self.payload)]
        )

    def test_if_send_shutdown_request_triggers_service_shutdown_callback(self):
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, 'shutdown_callback') as mock_shutdown_callback:
            self.service.listen()
        mock_shutdown_callback.assert_called_with(self.payload)

    def test_if_send_shutdown_request_triggers_service_plugin_shutdown_callback(self):
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service.service_plugin, 'shutdown_callback') as mock_shutdown_callback:
            self.service.listen()
        mock_shutdown_callback.assert_called_with(True, self.payload)

    def test_if_send_shutdown_request_triggers_service_shutdown_request_first_and_service_plugin_shutdown_request_second(self):
        manager = mock.MagicMock()
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, 'shutdown_callback') as mock_service_shutdown_callback:
            with mock.patch.object(self.service.service_plugin, 'shutdown_callback') as mock_service_plugin_shutdown_callback:
                manager.attach_mock(mock_service_shutdown_callback, 'mock_service_shutdown_callback')
                manager.attach_mock(mock_service_plugin_shutdown_callback, 'mock_service_plugin_shutdown_callback')
                self.service.listen()
        mock_service_shutdown_callback.assert_called_with(self.payload)
        mock_service_plugin_shutdown_callback.assert_called_with(True, self.payload)
        manager.assert_has_calls(
            [mock.call.mock_service_shutdown_callback(self.payload), mock.call.mock_service_plugin_shutdown_callback(True, self.payload)]
        )

    def test_if_send_request_triggers_service_request(self):
        self.service.send_request(self.payload)
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, '__call__', mock.Mock(return_value=(True, None))) as mock_service_request:
            self.service.listen()
        mock_service_request.assert_called_with(self.payload)

    def test_if_send_request_triggers_service_plugin_request(self):
        self.service.send_request(self.payload)
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, '__call__', mock.Mock(return_value=(True, None))) as mock_service_request:
            with mock.patch.object(self.service.service_plugin, '__call__') as mock_service_plugin_request:
                self.service.listen()
        mock_service_plugin_request.assert_called_with(True, self.payload, None)

    def test_if_send_request_triggers_service_request_first_and_service_plugin_request_second(self):
        manager = mock.MagicMock()
        self.service.send_request(self.payload)
        self.service.send_shutdown_request(self.payload)
        with mock.patch.object(self.service, '__call__', mock.Mock(return_value=(True, None))) as mock_service_request:
            with mock.patch.object(self.service.service_plugin, '__call__') as mock_service_plugin_request:
                manager.attach_mock(mock_service_request, 'mock_service_request')
                manager.attach_mock(mock_service_plugin_request, 'mock_service_plugin_request')
                self.service.listen()
        mock_service_request.assert_called_with(self.payload)
        mock_service_plugin_request.assert_called_with(True, self.payload, None)
        manager.assert_has_calls(
            [mock.call.mock_service_request(self.payload), mock.call.mock_service_plugin_request(True, self.payload, None)]
        )

    def test_if_service_does_not_process_any_other_requests_after_shutdown(self):
        self.service.send_shutdown_request(self.payload)
        self.assertEqual(self.service.keep_listening, True)
        self.service.listen()
        self.assertEqual(self.service.keep_listening, False)
        self.service.send_request(self.payload)
        with mock.patch.object(self.service.queue, 'get') as mock_queue_get:
            self.service.listen()
        mock_queue_get.assert_not_called()

    # TODO Implement unit tests for shutdown/request before startup, startup after startup, shutdown after shutdown etc.

if __name__ == '__main__':
    unittest.main()
