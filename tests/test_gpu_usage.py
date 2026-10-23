"""Hardware readings must describe the active speech worker, not the next job."""
import ctypes
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.jobs import Jobs
from backend.performance import Performance
from backend import gpu_usage


CPU = {'provider': 'CPUExecutionProvider', 'device_id': -1, 'threads': 2, 'label': 'CPU'}
GPU = {'provider': 'CUDAExecutionProvider', 'device_id': 0, 'threads': 2, 'label': 'Fixture GPU'}


class GpuPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.performance = Performance.__new__(Performance)
        self.performance.logical, self.performance.physical = 8, 4
        self.performance.store = SimpleNamespace(settings=lambda: {})
        self.performance.models = SimpleNamespace(gpu_error='')
        self.performance.resolve = Mock(return_value=CPU.copy())
        self.performance.gpu_devices = Mock(return_value=[])
        self.performance.gpu_ready = Mock(return_value=True)
        self.performance.recommendation = Mock(return_value=None)
        self.performance.usage = Mock(return_value=12.5)
        self.performance.benchmark, self.performance.warmup = {}, {}
        self.performance._gpu_usage = Mock()
        self.performance._gpu_usage.read.return_value = 61.7
        self.jobs = Jobs.__new__(Jobs)
        self.jobs.lock = threading.RLock()
        self.jobs.performance = self.performance
        self.jobs.process = SimpleNamespace(pid=321, is_alive=lambda: True)
        self.jobs.active = {'engine': GPU.copy()}
        self.jobs.operation, self.jobs.releasing, self.jobs.release_error = None, False, ''

    def test_gpu_reading_follows_active_job_when_next_reading_is_cpu(self):
        status = self.jobs.performance_state()
        self.assertEqual(status.get('gpu_percent'), 61.7)
        self.assertEqual(status['cpu_percent'], 12.5)
        self.assertEqual(status['configuration']['provider'], 'CPUExecutionProvider')
        self.performance._gpu_usage.read.assert_called_once_with(321)

    def test_cpu_job_never_reports_gpu_usage_even_if_next_reading_is_gpu(self):
        self.jobs.active = {'engine': CPU.copy()}
        self.performance.resolve.return_value = GPU.copy()
        status = self.jobs.performance_state()
        self.assertIn('gpu_percent', status)
        self.assertIsNone(status['gpu_percent'])
        self.performance._gpu_usage.read.assert_called_once_with(None)

    def test_unavailable_and_zero_measurements_remain_distinct(self):
        for value in (None, 0.0):
            with self.subTest(value=value):
                self.performance._gpu_usage.read.return_value = value
                status = self.jobs.performance_state()
                self.assertIn('gpu_percent', status)
                self.assertEqual(status['gpu_percent'], value)

    def test_idle_dead_and_legacy_workers_stop_gpu_sampling(self):
        for active, process in ((None, self.jobs.process),
                                ({'engine': GPU.copy()}, None),
                                ({'engine': GPU.copy()}, SimpleNamespace(pid=321, is_alive=lambda: False)),
                                ({}, self.jobs.process)):
            with self.subTest(active=active, process=process):
                self.jobs.active, self.jobs.process = active, process
                self.performance._gpu_usage.read.reset_mock()
                status = self.jobs.performance_state()
                self.assertIn('gpu_percent', status)
                self.assertIsNone(status['gpu_percent'])
                self.performance._gpu_usage.read.assert_called_once_with(None)

    def test_restarted_worker_uses_new_pid(self):
        self.jobs.performance_state()
        self.jobs.process = SimpleNamespace(pid=654, is_alive=lambda: True)
        self.jobs.performance_state()
        self.assertEqual([call.args for call in self.performance._gpu_usage.read.call_args_list], [(321,), (654,)])


class GpuCounterTests(unittest.TestCase):
    def test_busiest_valid_worker_engine_excludes_other_processes(self):
        rows = [('pid_321_luid_0_eng_0_engtype_Compute', 0, 23.4),
                ('pid_321_luid_0_eng_1_engtype_Copy', 1, 45.67),
                ('pid_3210_luid_0_eng_0_engtype_Compute', 0, 100),
                ('pid_999_luid_0_eng_0_engtype_Compute', 0, 99),
                ('pid_321_luid_0_eng_2_engtype_Compute', 0xC0000BBA, 97)]
        self.assertEqual(gpu_usage.busiest_engine(321, rows), 45.7)

    def test_missing_invalid_and_zero_values_are_distinct(self):
        self.assertIsNone(gpu_usage.busiest_engine(321, []))
        for value in (float('nan'), float('inf'), -1, 101):
            with self.subTest(value=value):
                self.assertIsNone(gpu_usage.busiest_engine(321, [('pid_321_engine', 0, value)]))
        self.assertEqual(gpu_usage.busiest_engine(321, [('pid_321_engine', 0, 0.0)]), 0.0)

    def query_fixture(self):
        query = gpu_usage._GpuQuery.__new__(gpu_usage._GpuQuery)
        query.query, query.counter = ctypes.c_void_p(99), ctypes.c_void_p(100)
        query.library = SimpleNamespace(PdhCollectQueryData=Mock(return_value=0),
                                        PdhGetFormattedCounterArrayW=Mock(), PdhCloseQuery=Mock())
        return query

    def test_native_array_reads_values_and_retries_a_changed_buffer(self):
        query = self.query_fixture()
        names = [ctypes.create_unicode_buffer('pid_321_engine'), ctypes.create_unicode_buffer('pid_999_engine')]
        attempts = 0

        def read(counter, fmt, size, count, buffer):
            nonlocal attempts
            self.assertEqual(fmt, gpu_usage.FORMAT_DOUBLE)
            size._obj.value, count._obj.value = 1024, 2
            if buffer is None:
                return gpu_usage.MORE_DATA
            attempts += 1
            if attempts == 1:
                return gpu_usage.MORE_DATA
            items = (gpu_usage._Item * 2).from_buffer(buffer)
            for index, value in enumerate((18.5, 99)):
                items[index].name = ctypes.cast(names[index], ctypes.c_wchar_p)
                items[index].value.status, items[index].value.number.double = 0, value
            return 0

        query.library.PdhGetFormattedCounterArrayW.side_effect = read
        self.assertEqual(query.read(), [('pid_321_engine', 0, 18.5), ('pid_999_engine', 0, 99)])
        self.assertEqual(attempts, 2)
        query.close()
        query.close()
        query.library.PdhCloseQuery.assert_called_once()

    def test_native_failure_and_no_data_cannot_reuse_old_values(self):
        query = self.query_fixture()
        query.library.PdhCollectQueryData.return_value = gpu_usage.NO_DATA
        self.assertEqual(query.read(), [])
        query.library.PdhGetFormattedCounterArrayW.assert_not_called()
        query.library.PdhCollectQueryData.return_value = 5
        with self.assertRaises(OSError):
            query.read()

    def test_native_buffer_allocation_is_bounded(self):
        query = self.query_fixture()

        def huge(counter, fmt, size, count, buffer):
            size._obj.value = 32 * 1024 * 1024
            return gpu_usage.MORE_DATA

        query.library.PdhGetFormattedCounterArrayW.side_effect = huge
        with self.assertRaises(OSError):
            query.read()

    def test_new_gpu_context_can_be_not_ready_then_supply_valid_data(self):
        for stage in ('collect', 'size', 'values'):
            for status in (0xC0000BBA, 0x800007D1):
                with self.subTest(stage=stage, status=status):
                    query = self.query_fixture()
                    name = ctypes.create_unicode_buffer('pid_321_engine')
                    waiting = True

                    def values(counter, fmt, size, count, buffer):
                        if waiting and stage == 'size':
                            return status
                        size._obj.value, count._obj.value = 1024, 1
                        if buffer is None:
                            return gpu_usage.MORE_DATA
                        if waiting and stage == 'values':
                            return status
                        item = gpu_usage._Item.from_buffer(buffer)
                        item.name = ctypes.cast(name, ctypes.c_wchar_p)
                        item.value.status, item.value.number.double = 0, 38.5
                        return 0

                    query.library.PdhGetFormattedCounterArrayW.side_effect = values
                    query.library.PdhCollectQueryData.return_value = status if stage == 'collect' else 0
                    try:
                        self.assertEqual(query.read(), [])
                    except OSError as error:
                        self.fail(f'A new GPU context must be allowed another rate sample: {error}')
                    waiting = False
                    query.library.PdhCollectQueryData.return_value = 0
                    self.assertEqual(query.read(), [('pid_321_engine', 0, 38.5)])

    def test_query_initialization_closes_handle_on_counter_failure(self):
        library = SimpleNamespace(PdhOpenQueryW=Mock(), PdhAddEnglishCounterW=Mock(return_value=5),
                                  PdhCollectQueryData=Mock(), PdhGetFormattedCounterArrayW=Mock(),
                                  PdhCloseQuery=Mock())

        def open_query(source, user, handle):
            handle._obj.value = 99
            return 0

        library.PdhOpenQueryW.side_effect = open_query
        with patch.object(gpu_usage.os, 'name', 'nt'), \
             patch.object(gpu_usage.ctypes, 'WinDLL', return_value=library, create=True) as load:
            with self.assertRaises(OSError):
                gpu_usage._GpuQuery(321)
        load.assert_called_once_with('pdh.dll', winmode=0x800)
        self.assertEqual(library.PdhAddEnglishCounterW.call_args.args[1],
                         r'\GPU Engine(pid_321_*)\Utilization Percentage')
        library.PdhCloseQuery.assert_called_once()


class GpuSamplerTests(unittest.TestCase):
    def run_counter_scenario(self, queries, duration, *, ui_polling=True, stop_at=None):
        """Drive real sampler logic with virtual time and disposable counter results."""
        monitor = gpu_usage.GpuUsage()
        clock, attempts, samples = [0.0], [], []
        stop = threading.Event()
        monitor._pid, monitor._stop = 321, stop
        choices = iter(queries)

        def open_query(pid):
            self.assertEqual(pid, 321)
            attempts.append(clock[0])
            query = next(choices)
            if isinstance(query, Exception):
                raise query
            return query

        def wait(seconds):
            samples.append((clock[0], monitor._percent))
            clock[0] += seconds
            if ui_polling:
                monitor._requested = clock[0]
            if clock[0] >= (duration if stop_at is None else stop_at):
                stop.set()
            return stop.is_set()

        with patch.object(gpu_usage.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(gpu_usage, '_GpuQuery', side_effect=open_query), \
             patch.object(stop, 'wait', side_effect=wait):
            monitor._poll(321, stop)
        return monitor, attempts, samples

    def test_counter_creation_failure_recovers_without_changing_worker(self):
        healthy = Mock()
        healthy.read.return_value = [('pid_321_engine', 0, 38.5)]
        monitor, attempts, _ = self.run_counter_scenario(
            [OSError('Temporary PDH failure'), healthy], 9)
        self.assertEqual(attempts, [0, 5])
        self.assertEqual(monitor._percent, 38.5)
        healthy.close.assert_called_once()

    def test_counter_read_failure_clears_old_value_then_recovers_with_real_zero(self):
        broken, healthy = Mock(), Mock()
        broken.read.side_effect = [[('pid_321_engine', 0, 72)], OSError('Counter was lost')]
        healthy.read.return_value = [('pid_321_engine', 0, 0.0)]
        monitor, attempts, samples = self.run_counter_scenario([broken, healthy], 10)
        self.assertEqual(attempts, [0, 7])
        self.assertIn((1, 72), samples)
        self.assertTrue(all(value is None for when, value in samples if 2 <= when <= 7))
        self.assertEqual(monitor._percent, 0.0)
        broken.close.assert_called_once()
        healthy.close.assert_called_once()

    def test_repeated_counter_failures_back_off_to_thirty_seconds(self):
        failures = [OSError('Unsupported counter') for _ in range(5)]
        monitor, attempts, samples = self.run_counter_scenario(failures, 66)
        self.assertEqual(attempts, [0, 5, 15, 35, 65])
        self.assertIsNone(monitor._percent)
        self.assertTrue(all(value is None for _, value in samples))

    def test_successful_sample_resets_backoff_before_a_later_failure(self):
        intermittent, healthy = Mock(), Mock()
        intermittent.read.side_effect = [[('pid_321_engine', 0, 21)], ValueError('Counter reset')]
        healthy.read.return_value = [('pid_321_engine', 0, 48)]
        monitor, attempts, _ = self.run_counter_scenario(
            [OSError('First failure'), OSError('Second failure'), intermittent, healthy], 25)
        self.assertEqual(attempts, [0, 5, 15, 22])
        self.assertEqual(monitor._percent, 48)
        intermittent.close.assert_called_once()
        healthy.close.assert_called_once()

    def test_counter_retries_end_when_ui_becomes_idle(self):
        monitor, attempts, _ = self.run_counter_scenario(
            [OSError('Temporary failure'), OSError('Still unavailable')], 40, ui_polling=False)
        self.assertEqual(attempts, [0, 5])
        self.assertIsNone(monitor._pid)
        self.assertIsNone(monitor._percent)

    def test_stopping_during_retry_delay_prevents_reopening(self):
        healthy = Mock()
        monitor, attempts, _ = self.run_counter_scenario(
            [OSError('Temporary failure'), healthy], 20, stop_at=2)
        self.assertEqual(attempts, [0])
        self.assertIsNone(monitor._percent)
        healthy.read.assert_not_called()
        healthy.close.assert_not_called()

    def wait_until(self, condition):
        deadline = time.perf_counter() + 2
        while not condition() and time.perf_counter() < deadline:
            time.sleep(.005)
        self.assertTrue(condition())

    def test_sampling_is_nonblocking_and_stopping_closes_query(self):
        opened, sampling, release, closed = (threading.Event() for _ in range(4))

        def sample():
            sampling.set()
            release.wait(2)
            return [('pid_321_engine', 0, 42)]

        query = SimpleNamespace(read=sample, close=closed.set)
        monitor = gpu_usage.GpuUsage()
        with patch.object(gpu_usage, 'SAMPLE_SECONDS', .01), \
             patch.object(gpu_usage, '_GpuQuery', side_effect=lambda pid: (opened.set() or query)):
            try:
                self.assertIsNone(monitor.read(321))
                self.assertTrue(opened.wait(1))
                self.assertTrue(sampling.wait(1))
                self.assertIsNone(monitor.read(321))
                release.set()
                self.wait_until(lambda: monitor.read(321) == 42)
            finally:
                monitor.read(None)
                release.set()
                self.assertTrue(closed.wait(1))

    def test_old_worker_cannot_publish_over_new_worker(self):
        old_sampling, release, old_closed, new_closed = (threading.Event() for _ in range(4))

        def old_sample():
            old_sampling.set()
            release.wait(2)
            return [('pid_321_engine', 0, 99)]

        old = SimpleNamespace(read=old_sample, close=old_closed.set)
        new = SimpleNamespace(read=lambda: [('pid_654_engine', 0, 12)], close=new_closed.set)
        monitor = gpu_usage.GpuUsage()
        with patch.object(gpu_usage, 'SAMPLE_SECONDS', .01), \
             patch.object(gpu_usage, '_GpuQuery', side_effect=lambda pid: old if pid == 321 else new):
            try:
                monitor.read(321)
                self.assertTrue(old_sampling.wait(1))
                self.assertIsNone(monitor.read(654))
                self.wait_until(lambda: monitor.read(654) == 12)
                release.set()
                self.assertTrue(old_closed.wait(1))
                self.assertEqual(monitor.read(654), 12)
            finally:
                monitor.read(None)
                release.set()
                self.assertTrue(new_closed.wait(1))

    def test_stale_readings_are_hidden_and_no_pid_starts_no_thread(self):
        monitor = gpu_usage.GpuUsage()
        with patch.object(gpu_usage.threading, 'Thread') as thread:
            self.assertIsNone(monitor.read(None))
            thread.assert_not_called()
            monitor._pid, monitor._percent = 321, 55
            monitor._updated = time.monotonic() - gpu_usage.MAX_AGE_SECONDS - 1
            self.assertIsNone(monitor.read(321))
            thread.assert_not_called()
            self.assertIsNone(monitor.read(None))

    def test_failed_counter_is_optional_and_does_not_restart_on_every_poll(self):
        attempted = threading.Event()

        def unavailable(pid):
            attempted.set()
            raise OSError('Disposable unsupported counter')

        monitor = gpu_usage.GpuUsage()
        with patch.object(gpu_usage, '_GpuQuery', side_effect=unavailable) as query:
            self.assertIsNone(monitor.read(321))
            self.assertTrue(attempted.wait(1))
            self.assertIsNone(monitor.read(321))
            query.assert_called_once_with(321)
            monitor.read(None)

    def assert_idle_sampler_closes(self, *, start_delay=0):
        opened, closed = threading.Event(), threading.Event()
        monitor = gpu_usage.GpuUsage()
        query = SimpleNamespace(read=lambda: [], close=Mock(side_effect=closed.set))
        threads = []

        def create_thread(*args, **kwargs):
            if start_delay:
                target = kwargs['target']

                def delayed(*target_args, **target_kwargs):
                    # Deliberately hold startup beyond the fixture's idle limit.
                    threading.Event().wait(start_delay)
                    return target(*target_args, **target_kwargs)

                kwargs['target'] = delayed
            thread = threading.Thread(*args, **kwargs)
            threads.append(thread)
            return thread

        local_threading = SimpleNamespace(Lock=threading.Lock, Event=threading.Event,
                                          Thread=create_thread)

        def open_query(pid):
            opened.set()
            return query

        with patch.object(gpu_usage, 'SAMPLE_SECONDS', .01), patch.object(gpu_usage, 'IDLE_SECONDS', .02), \
             patch.object(gpu_usage, 'threading', local_threading), \
             patch.object(gpu_usage, '_GpuQuery', side_effect=open_query) as factory:
            try:
                monitor.read(321)
                deadline = time.perf_counter() + 1
                while not opened.wait(.005):
                    self.assertLess(time.perf_counter(), deadline, 'GPU counter did not open.')
                    monitor.read(321)
                # Stop refreshing only once there is a query whose idle close is observable.
                self.assertTrue(closed.wait(1))
                self.assertIsNone(monitor._pid)
                factory.assert_called_once_with(321)
                query.close.assert_called_once_with()
            finally:
                monitor.read(None)
                for thread in threads:
                    thread.join(1)
                    self.assertFalse(thread.is_alive(), 'GPU sampler survived fixture cleanup.')

    def test_sampler_releases_counter_when_ui_stops_polling(self):
        self.assert_idle_sampler_closes()

    def test_sampler_releases_counter_after_delayed_thread_start(self):
        self.assert_idle_sampler_closes(start_delay=.05)


if __name__ == '__main__':
    unittest.main()
