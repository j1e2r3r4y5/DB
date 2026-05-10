"""
Unit tests for DataScheduler enhancements
"""

import unittest
import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_scheduler import DataScheduler, DataCollectionJob


class TestDataCollectionJob(unittest.TestCase):
    def test_job_initialization(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)

        self.assertEqual(job.job_id, "job1")
        self.assertEqual(job.slave_id, 1)
        self.assertEqual(job.func_code, 3)
        self.assertEqual(job.start_addr, 0)
        self.assertEqual(job.quantity, 10)
        self.assertEqual(job.interval, 5.0)
        self.assertTrue(job.enabled)
        self.assertIsNone(job.last_run)

    def test_should_run_initially(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.assertTrue(job.should_run())

    def test_should_run_when_disabled(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        job.enabled = False
        self.assertFalse(job.should_run())

    def test_should_run_after_interval(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 0.1)
        self.assertTrue(job.should_run())
        job.mark_run()
        self.assertFalse(job.should_run())
        time.sleep(0.15)
        self.assertTrue(job.should_run())

    def test_mark_run_updates_time(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.assertIsNone(job.last_run)
        job.mark_run()
        self.assertIsNotNone(job.last_run)


class TestDataScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = DataScheduler()

    def tearDown(self):
        if self.scheduler.is_running:
            self.scheduler.stop()

    def test_add_job(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        result = self.scheduler.add_job(job)
        self.assertTrue(result)
        self.assertEqual(len(self.scheduler.get_all_jobs()), 1)

    def test_add_duplicate_job(self):
        job1 = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        job2 = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.scheduler.add_job(job1)
        result = self.scheduler.add_job(job2)
        self.assertFalse(result)
        self.assertEqual(len(self.scheduler.get_all_jobs()), 1)

    def test_remove_job(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.scheduler.add_job(job)
        result = self.scheduler.remove_job("job1")
        self.assertTrue(result)
        self.assertEqual(len(self.scheduler.get_all_jobs()), 0)

    def test_remove_nonexistent_job(self):
        result = self.scheduler.remove_job("nonexistent")
        self.assertFalse(result)

    def test_enable_job(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        job.enabled = False
        self.scheduler.add_job(job)
        result = self.scheduler.enable_job("job1")
        self.assertTrue(result)
        self.assertTrue(self.scheduler.get_job("job1").enabled)

    def test_disable_job(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.scheduler.add_job(job)
        result = self.scheduler.disable_job("job1")
        self.assertTrue(result)
        self.assertFalse(self.scheduler.get_job("job1").enabled)

    def test_update_job_interval(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.scheduler.add_job(job)

        result = self.scheduler.update_job_interval("job1", 10.0)
        self.assertTrue(result)
        self.assertEqual(self.scheduler.get_job("job1").interval, 10.0)

    def test_update_job_interval_minimum(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        self.scheduler.add_job(job)

        self.scheduler.update_job_interval("job1", 0.1)
        self.assertEqual(self.scheduler.get_job("job1").interval, 1.0)

    def test_update_all_intervals(self):
        job1 = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        job2 = DataCollectionJob("job2", 1, 4, 0, 10, 10.0)
        self.scheduler.add_job(job1)
        self.scheduler.add_job(job2)

        count = self.scheduler.update_all_intervals(15.0)
        self.assertEqual(count, 2)
        self.assertEqual(self.scheduler.get_job("job1").interval, 15.0)
        self.assertEqual(self.scheduler.get_job("job2").interval, 15.0)

    def test_get_statistics(self):
        job1 = DataCollectionJob("job1", 1, 3, 0, 10, 5.0)
        job2 = DataCollectionJob("job2", 1, 4, 0, 10, 10.0)
        job2.enabled = False
        self.scheduler.add_job(job1)
        self.scheduler.add_job(job2)

        stats = self.scheduler.get_statistics()
        self.assertEqual(stats["total_jobs"], 2)
        self.assertEqual(stats["enabled_jobs"], 1)
        self.assertEqual(stats["disabled_jobs"], 1)
        self.assertFalse(stats["running"])

    def test_start_stop(self):
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)

    def test_start_twice(self):
        self.scheduler.start()
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)
        self.scheduler.stop()


class TestDataSchedulerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.scheduler = DataScheduler()

    def tearDown(self):
        if self.scheduler.is_running:
            self.scheduler.stop()

    def test_job_with_zero_interval(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 0.0)
        self.scheduler.add_job(job)
        self.scheduler.update_job_interval("job1", 0.0)
        self.assertEqual(self.scheduler.get_job("job1").interval, 1.0)

    def test_concurrent_job_access(self):
        job = DataCollectionJob("job1", 1, 3, 0, 10, 0.01)
        self.scheduler.add_job(job)

        errors = []

        def add_remove_jobs():
            try:
                for i in range(100):
                    self.scheduler.add_job(DataCollectionJob(f"job{i}", 1, 3, 0, 10, 5.0))
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def update_intervals():
            try:
                for i in range(100):
                    self.scheduler.update_all_intervals(5.0 + i)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=add_remove_jobs)
        t2 = threading.Thread(target=update_intervals)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
