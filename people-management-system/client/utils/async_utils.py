"""
Async Utility Functions for Qt + HTTP Client Integration

This module provides utilities to safely handle HTTP operations within Qt applications,
avoiding event loop conflicts and ensuring proper HTTP client lifecycle management.

NOTE: This has been updated to work with synchronous HTTP clients to avoid
event loop management issues in Qt applications.
"""

import asyncio
import inspect
import logging
from typing import Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import threading

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class SyncTaskWorker(QThread):
    """Worker thread for executing synchronous tasks safely within Qt applications."""
    
    # Signals
    finished = Signal(object)  # Result of the operation
    error = Signal(Exception)  # Error that occurred
    progress = Signal(str)     # Progress message
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.exception = None
    
    def run(self):
        """Execute the function (sync or async)."""
        try:
            # Check if function is None
            if self.func is None:
                logger.error("Task failed: Function is None")
                self.exception = ValueError("Function is None")
                self.error.emit(self.exception)
                return
            
            # Check if the function is a coroutine or async function
            if inspect.iscoroutinefunction(self.func):
                # Run async function in new event loop
                self.result = asyncio.run(self.func(*self.args, **self.kwargs))
            elif inspect.iscoroutine(self.func):
                # It's already a coroutine object, run it
                self.result = asyncio.run(self.func)
            else:
                # Regular synchronous function
                self.result = self.func(*self.args, **self.kwargs)
            
            self.finished.emit(self.result)
            
        except Exception as e:
            logger.error(f"Task failed: {e}")
            self.exception = e
            self.error.emit(e)


class SyncRunner(QObject):
    """
    Helper class to run synchronous operations safely in Qt applications.
    
    This class runs synchronous functions in worker threads to avoid blocking
    the Qt GUI event loop.
    """
    
    # Signals
    task_completed = Signal(object)  # Result
    task_failed = Signal(Exception)  # Error
    task_progress = Signal(str)      # Progress update
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.active_workers = []
        
    def run_sync(self, func, *args, 
                 on_success: Optional[Callable[[Any], None]] = None,
                 on_error: Optional[Callable[[Exception], None]] = None,
                 **kwargs) -> SyncTaskWorker:
        """
        Run a synchronous function safely within a Qt application.
        
        Args:
            func: The function to execute
            *args: Positional arguments for the function
            on_success: Callback for successful completion
            on_error: Callback for errors
            **kwargs: Keyword arguments for the function
            
        Returns:
            SyncTaskWorker instance
        """
        worker = SyncTaskWorker(func, *args, **kwargs)
        
        # Connect signals
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        
        if on_success:
            worker.finished.connect(on_success)
        if on_error:
            worker.error.connect(on_error)
        
        # Track worker
        self.active_workers.append(worker)
        
        # Start worker
        worker.start()
        
        return worker
    
    def _on_worker_finished(self, result):
        """Handle worker completion."""
        worker = self.sender()
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        self.task_completed.emit(result)
        worker.deleteLater()
    
    def _on_worker_error(self, error):
        """Handle worker error."""
        worker = self.sender()
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        self.task_failed.emit(error)
        worker.deleteLater()
    
    def wait_for_completion(self, timeout_ms: int = 30000):
        """Wait for all active workers to complete."""
        for worker in self.active_workers[:]:
            if worker.isRunning():
                worker.quit()
                worker.wait(timeout_ms)


def run_sync_in_qt(func, *args,
                   on_success: Optional[Callable[[Any], None]] = None,
                   on_error: Optional[Callable[[Exception], None]] = None,
                   **kwargs) -> SyncTaskWorker:
    """
    Convenience function to run synchronous functions safely in Qt applications.
    
    This function creates a temporary SyncRunner and executes the function.
    For multiple operations, it's better to create a persistent SyncRunner instance.
    
    Args:
        func: The function to execute
        *args: Positional arguments
        on_success: Callback for successful completion  
        on_error: Callback for errors
        **kwargs: Keyword arguments
        
    Returns:
        SyncTaskWorker instance
    """
    runner = SyncRunner()
    return runner.run_sync(func, *args, on_success=on_success, on_error=on_error, **kwargs)


def is_event_loop_running() -> bool:
    """Check if an asyncio event loop is currently running."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def safe_sync_run(func, *args, **kwargs):
    """
    Safely run a synchronous function, typically in a thread pool if needed.
    
    This should only be used for simple cases. For Qt applications, prefer
    run_sync_in_qt or SyncRunner.
    """
    try:
        # For Qt applications, it's better to use worker threads
        # but for simple cases, we can run directly
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Failed to run sync operation: {e}")
        raise


class QtSyncHelper:
    """
    Helper class for integrating synchronous operations with Qt widgets.
    
    This class provides methods to run synchronous operations in worker threads
    while properly handling Qt signals and slots.
    """
    
    def __init__(self, parent_widget=None):
        self.parent = parent_widget
        self.runner = SyncRunner(parent_widget)
        
    def call_sync(self, func, *args, success_callback=None, error_callback=None, **kwargs):
        """Call a synchronous function and handle the result with callbacks."""
        if func is None:
            logger.error("Cannot call None function")
            if error_callback:
                error_callback(ValueError("Function is None"))
            return None
        return self.runner.run_sync(func, *args, on_success=success_callback, on_error=error_callback, **kwargs)
    
    def call_sync_method(self, method, *args, **kwargs):
        """Call a synchronous method with arguments."""
        return self.call_sync(method, *args, **kwargs)
    
    def cleanup(self):
        """Clean up resources."""
        if self.runner:
            self.runner.wait_for_completion()


# Global sync runner for convenience
_global_runner = None

def get_global_sync_runner() -> SyncRunner:
    """Get a global SyncRunner instance for convenience."""
    global _global_runner
    if _global_runner is None:
        _global_runner = SyncRunner()
    return _global_runner


def cleanup_global_runner():
    """Clean up the global async runner."""
    global _global_runner
    if _global_runner:
        _global_runner.wait_for_completion()
        _global_runner = None