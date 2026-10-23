"""A successful recording removal must win over older persistence retries."""
import copy
import queue
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store
from tests.test_pcm_audio import pcm


class RecordingRemovalRetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='violilt-removal-retry-')
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'library')
        with patch('backend.jobs.threading.Thread'):
            self.jobs = Jobs(self.store, None)
        self.addCleanup(self.cleanup_jobs)
        self.bridge = Bridge(self.store, None, self.jobs)
        clock = patch('backend.jobs.time.monotonic', return_value=10)
        self.clock = clock.start()
        self.addCleanup(clock.stop)

    def cleanup_jobs(self):
        self.jobs.active = None
        self.jobs.close()
        for channel in (self.jobs.commands, self.jobs.events):
            channel.cancel_join_thread()
            channel.close()

    def recording(self, state='failed'):
        job = {'id': uuid.uuid4().hex, 'title': 'Synthetic pending recording', 'created': 1,
               'state': state, 'completed': 0, 'total': 1, 'duration': 0, 'position': 0,
               'voice': 'af_heart', 'speed': 1, 'message': 'Original saved status.'}
        self.store.put('jobs', job)
        directory = self.store.root / 'jobs' / job['id']
        directory.mkdir()
        audio = directory / 'recording.wav'
        audio.write_bytes(pcm())
        return job, audio

    def pending(self, job):
        latest = job | {'message': 'Latest pending terminal status.'}
        self.clock.return_value += 3
        with self.jobs.lock, patch.object(self.store, 'put', side_effect=sqlite3.OperationalError('Synthetic transient write failure')) as write:
            self.jobs._save_progress(latest)
            self.assertEqual(write.call_count, 1)
        self.assertEqual(self.jobs.pending_storage()['job'], latest)
        return latest

    def absent(self, key):
        self.assertNotIn(key, [job['id'] for job in self.store.all('jobs')])

    def test_successful_removal_stays_removed_after_retry_for_both_audio_choices(self):
        for state in ('failed', 'cancelled'):
            for delete_audio in (False, True):
                with self.subTest(state=state, delete_audio=delete_audio):
                    job, audio = self.recording(state)
                    self.pending(job)
                    self.assertTrue(self.bridge.remove_recording(job['id'], delete_audio))
                    self.absent(job['id'])
                    self.assertEqual(audio.exists(), not delete_audio)
                    self.clock.return_value += 3
                    with self.jobs.lock:
                        self.jobs._flush_persistence()
                    self.absent(job['id'])

    def test_removing_last_pending_recording_clears_obsolete_warning_and_retry(self):
        job, _ = self.recording()
        self.pending(job)
        self.bridge.remove_recording(job['id'])
        self.assertEqual(self.jobs.pending_storage(), {'job': None, 'message': ''})
        self.assertEqual(self.jobs._persistence_retry_at, 0)

    def test_retry_before_removal_also_leaves_recording_absent(self):
        for delete_audio in (False, True):
            with self.subTest(delete_audio=delete_audio):
                job, audio = self.recording()
                latest = self.pending(job)
                self.clock.return_value += 3
                with self.jobs.lock:
                    self.jobs._flush_persistence()
                self.assertEqual(self.store.get('jobs', job['id'])['message'], latest['message'])
                self.bridge.remove_recording(job['id'], delete_audio)
                with self.jobs.lock:
                    self.jobs._flush_persistence(force=True)
                self.absent(job['id'])
                self.assertEqual(audio.exists(), not delete_audio)

    def test_failed_database_deletion_preserves_pending_snapshot_for_both_audio_choices(self):
        for delete_audio in (False, True):
            with self.subTest(delete_audio=delete_audio):
                job, audio = self.recording()
                latest = self.pending(job)
                warning, retry_at = self.jobs.persistence_error, self.jobs._persistence_retry_at
                with patch.object(self.store, 'remove', side_effect=sqlite3.OperationalError('Synthetic delete failure')):
                    with self.assertRaises(sqlite3.OperationalError):
                        self.bridge.remove_recording(job['id'], delete_audio)
                self.assertEqual(self.jobs.pending_storage()['job'], latest)
                self.assertEqual((self.jobs.persistence_error, self.jobs._persistence_retry_at), (warning, retry_at))
                self.assertEqual(self.store.get('jobs', job['id'])['id'], job['id'])
                # Existing audio-before-row order is not a filesystem transaction.
                self.assertEqual(audio.exists(), not delete_audio)

    def test_failed_audio_deletion_preserves_row_and_pending_metadata(self):
        job, audio = self.recording()
        latest = self.pending(job)
        with patch('backend.bridge.shutil.rmtree', side_effect=PermissionError('Synthetic audio deletion failure')):
            with self.assertRaises(PermissionError):
                self.bridge.remove_recording(job['id'], True)
        self.assertTrue(audio.exists())
        self.assertEqual(self.store.get('jobs', job['id'])['id'], job['id'])
        self.assertEqual(self.jobs.pending_storage()['job'], latest)

    def test_removing_other_recording_keeps_unrelated_pending_update_and_warning(self):
        pending_job, _ = self.recording()
        removed_job, _ = self.recording()
        latest = self.pending(pending_job)
        warning, retry_at = self.jobs.persistence_error, self.jobs._persistence_retry_at
        self.bridge.remove_recording(removed_job['id'])
        self.assertEqual(self.jobs.pending_storage()['job'], latest)
        self.assertEqual((self.jobs.persistence_error, self.jobs._persistence_retry_at), (warning, retry_at))
        self.clock.return_value += 3
        with self.jobs.lock:
            self.jobs._flush_persistence()
        self.assertEqual(self.store.get('jobs', pending_job['id'])['message'], latest['message'])
        self.absent(removed_job['id'])

    def test_pending_benchmark_is_preserved_and_warning_clears_only_after_it_saves(self):
        job, _ = self.recording()
        self.pending(job)
        benchmark = {'identity': 'synthetic-speed-test', 'cpu': {'threads': 1},
                     'best': {'threads': 1, 'provider': 'CPUExecutionProvider'}}
        self.jobs._pending_benchmark = copy.deepcopy(benchmark)
        warning, retry_at = self.jobs.persistence_error, self.jobs._persistence_retry_at
        self.bridge.remove_recording(job['id'])
        self.assertEqual(self.jobs.pending_storage()['job'], None)
        self.assertEqual(self.jobs._pending_benchmark, benchmark)
        self.assertEqual((self.jobs.persistence_error, self.jobs._persistence_retry_at), (warning, retry_at))
        self.clock.return_value += 3
        with self.jobs.lock:
            self.jobs._flush_persistence()
        self.assertEqual(self.store.settings()['benchmark_result'], benchmark)
        self.assertEqual(self.jobs.pending_storage(), {'job': None, 'message': ''})
        self.absent(job['id'])

    def test_active_recording_remains_protected(self):
        job, audio = self.recording()
        latest = self.pending(job)
        self.jobs.active = job | {'state': 'generating'}
        with self.assertRaisesRegex(ValueError, 'Stop this reading'):
            self.bridge.remove_recording(job['id'], True)
        self.assertTrue(audio.exists())
        self.assertEqual(self.jobs.pending_storage()['job'], latest)
        self.assertEqual(self.store.get('jobs', job['id'])['id'], job['id'])

    def test_late_worker_event_does_not_recreate_removed_recording(self):
        job, _ = self.recording()
        self.pending(job)
        self.bridge.remove_recording(job['id'])
        self.clock.return_value += 3
        original_events = self.jobs.events
        events = iter([{'id': job['id'], 'state': 'failed'}])

        def get(timeout):
            try:
                return next(events)
            except StopIteration:
                self.jobs.closing = True
                raise queue.Empty()

        from types import SimpleNamespace
        self.jobs.events = SimpleNamespace(get=get)
        try:
            self.jobs._listen()
        finally:
            self.jobs.events = original_events
        self.absent(job['id'])

    def test_shutdown_does_not_flush_removed_recording_back_into_library(self):
        job, _ = self.recording()
        self.pending(job)
        self.bridge.remove_recording(job['id'])
        self.jobs.close()
        self.absent(job['id'])
