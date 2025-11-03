import concurrent.futures


class FastShutdownThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    """ThreadPoolExecutor with modified __exit__ method to shut down the executor without waiting.

    This allows the `with` block to immediately exit on error, rather than waiting for all threads to finish their
    work in progress. This is useful when the work is not critical and we want to exit the `with` block as soon as
    possible so we can, for example, catch the exception as soon as possible.

    Note that futures already running will continue to run, but the error will be raised immediately.
    """

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=False)
        return False
