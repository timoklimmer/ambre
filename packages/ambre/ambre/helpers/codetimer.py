"""Provides a context manager to time code blocks."""

import pandas as pd
import timeit

class CodeTimer:
    """Context manager to time a code block."""

    def __init__(self, activity_name=None):
        """Init."""
        self.start = None
        self.activity_name = activity_name

    def __enter__(self):
        """Start timing when context is entered."""
        self.start = timeit.default_timer()
        if self.activity_name:
            print(f"{self.activity_name}...")

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit timing when context is exited."""
        ms_taken = (timeit.default_timer() - self.start) * 1000.0
        pd_time_delta = pd.to_timedelta(ms_taken, unit="ms")
        print(f"Time taken: {pd_time_delta}.\n")
