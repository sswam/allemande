#!/usr/bin/env python3

import threading
import time

from thread_safe_dict import ThreadSafeDict

def test_thread_safe_dict():
    # Create a thread-safe dictionary
    d = ThreadSafeDict()

    def writer():
        for i in range(100000):
            d[i] = i
            # time.sleep(0.01)

    def reader():
        for i in range(100000):
            _ = d.get(i, None)
            # time.sleep(0.01)

    # Create multiple threads that read and write
    threads = []
    for _ in range(3):
        threads.append(threading.Thread(target=writer))
        threads.append(threading.Thread(target=reader))

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print(f"Final dictionary size: {len(d)}")

# Run the test
if __name__ == "__main__":
    test_thread_safe_dict()
