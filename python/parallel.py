#!/usr/bin/env python3

import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

def process_text(text):
    time.sleep(3)  # Simulate work
    return f"Processed: {text}"

def parallel_process(texts, pool):
    with ProcessPoolExecutor(max_workers=pool) as executor:
        future_to_text = {executor.submit(process_text, text): text for text in texts}
        for future in as_completed(future_to_text):
            original_text = future_to_text[future]
            try:
                result = future.result()
                print(f"Original: {original_text}, Result: {result}")
            except Exception as exc:
                print(f'Generated an exception: {exc}')

def main():
    texts = ["Text1", "Text2", "Text3", "Text4"]
    pool = 2  # Number of parallel processes

    start_time = time.time()
    parallel_process(texts, pool)
    end_time = time.time()

    print(f"Total time: {end_time - start_time} seconds")

if __name__ == "__main__":
    main()
