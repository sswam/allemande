I'm guess it's unsafe to run a Python regexp (re or regex) from an untrusted source. What's the worst they can do, denial of sevice through being slow / using too much CPU?
Please reply as concise as possible, with no boilerplate or unnecessary explanation.

Beyond DoS attacks, certain regex patterns can cause catastrophic backtracking or excessive memory usage. However, they can't execute arbitrary code or escape the regex engine's sandbox. The main risks are resource exhaustion (CPU/memory) and application hanging.

I'm guess it's unsafe to run a Python regexp (re or regex) from an untrusted source. What's the worst they can do, denial of sevice through being slow / using too much CPU? How to protect against it?
Please reply as concise as possible, with no boilerplate or unnecessary explanation.

Beyond DoS through catastrophic backtracking (exponential time complexity), Python regexes are generally safe. They can't execute arbitrary code or access the filesystem.

To protect against DoS:
1. Use timeout (via signal.alarm on Unix or threading.Timer)
2. Limit input string length
3. Limit regex pattern length
4. Use non-backtracking engines like `re2` library instead of `re`

Example timeout:
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError()

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(1)  # 1 second timeout
try:
    result = re.match(unsafe_pattern, text)
finally:
    signal.alarm(0)
```

