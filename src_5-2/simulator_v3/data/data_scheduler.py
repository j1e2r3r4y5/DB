from typing import Dict, List, Callable, Optional
import threading
import time
import logging

from data.virtual_device import VirtualDevice
from core.modbus_master import ModbusMaster

logger = logging.getLogger(__name__)


class DataCollectionJob:
    def __init__(
        self,
        job_id: str,
        slave_id: int,
        func_code: int,
        start_addr: int,
        quantity: int,
        interval: float
    ):
        self.job_id = job_id
        self.slave_id = slave_id
        self.func_code = func_code
        self.start_addr = start_addr
        self.quantity = quantity
        self.interval = interval
        self.last_run: Optional[float] = None
        self.enabled = True
        self._lock = threading.Lock()

    def should_run(self) -> bool:
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        return (time.time() - self.last_run) >= self.interval

    def mark_run(self):
        with self._lock:
            self.last_run = time.time()


class DataScheduler:
    def __init__(self, modbus_master: Optional[ModbusMaster] = None):
        self.modbus_master = modbus_master
        self._jobs: Dict[str, DataCollectionJob] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._on_data_callback: Optional[Callable[[str, int, int, int, int, bytes], None]] = None

    def set_modbus_master(self, modbus_master: ModbusMaster):
        self.modbus_master = modbus_master

    def set_on_data_callback(self, callback: Callable[[str, int, int, int, int, bytes], None]):
        self._on_data_callback = callback

    def add_job(self, job: DataCollectionJob) -> bool:
        with self._lock:
            if job.job_id in self._jobs:
                logger.warning(f"Job {job.job_id} already exists")
                return False
            self._jobs[job.job_id] = job
            logger.info(f"Added job: {job.job_id} (slave={job.slave_id}, interval={job.interval}s)")
            return True

    def remove_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.info(f"Removed job: {job_id}")
                return True
            return False

    def get_job(self, job_id: str) -> Optional[DataCollectionJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def enable_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.enabled = True
                return True
            return False

    def disable_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.enabled = False
                return True
            return False

    def update_job_interval(self, job_id: str, interval: float) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                old_interval = job.interval
                job.interval = max(1.0, interval)
                logger.info(f"Updated job {job_id} interval: {old_interval}s -> {job.interval}s")
                return True
            return False

    def update_all_intervals(self, interval: float) -> int:
        with self._lock:
            count = 0
            for job_id, job in self._jobs.items():
                job.interval = max(1.0, interval)
                count += 1
            if count > 0:
                logger.info(f"Updated all {count} jobs interval to {interval}s")
            return count

    def get_statistics(self) -> Dict:
        with self._lock:
            total = len(self._jobs)
            enabled = sum(1 for job in self._jobs.values() if job.enabled)
            disabled = total - enabled
            return {
                "total_jobs": total,
                "enabled_jobs": enabled,
                "disabled_jobs": disabled,
                "running": self._running
            }

    def start(self):
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Data scheduler started")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Data scheduler stopped")

    def _run_loop(self):
        while self._running:
            try:
                self._check_and_execute_jobs()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            time.sleep(1.0)

    def _check_and_execute_jobs(self):
        with self._lock:
            jobs_to_run = [(job_id, job) for job_id, job in self._jobs.items() if job.should_run()]

        for job_id, job in jobs_to_run:
            self._execute_job(job)

    def _execute_job(self, job: DataCollectionJob):
        if not self.modbus_master:
            logger.warning(f"No Modbus master configured, cannot execute job {job.job_id}")
            return

        try:
            data = self.modbus_master.read(
                slave_id=job.slave_id,
                func_code=job.func_code,
                start_addr=job.start_addr,
                quantity=job.quantity
            )

            if data is not None:
                job.mark_run()
                logger.debug(f"Job {job.job_id} executed successfully")

                if self._on_data_callback:
                    self._on_data_callback(
                        job.job_id,
                        job.slave_id,
                        job.func_code,
                        job.start_addr,
                        job.quantity,
                        data
                    )
            else:
                logger.warning(f"Job {job.job_id} failed: no data received")

        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {e}")

    def get_all_jobs(self) -> List[DataCollectionJob]:
        with self._lock:
            return list(self._jobs.values())

    @property
    def is_running(self) -> bool:
        return self._running