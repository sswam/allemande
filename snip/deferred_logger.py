class DeferredLogger(logging.LoggerAdapter):
    def __init__(self, name):
        super().__init__(logging.getLogger('dummy'), {})
        self._name = name
        self.dummy_logger = logging.getLogger('dummy')
        self.real_logger = None
        self.deferred_messages = deque()
        self.is_real_logger_set = False

    @property
    def name(self):
        return self._name

    def __getattr__(self, name):
        if not self.is_real_logger_set and logging.getLogger(self.name) is not logging.root:
            self.set_real_logger(logging.getLogger(self.name))
        return getattr(self.real_logger or self.dummy_logger, name)

    def set_real_logger(self, logger):
        self.real_logger = logger
        self.is_real_logger_set = True
        self._forward_deferred_messages()

    def _forward_deferred_messages(self):
        while self.deferred_messages:
            level, msg, args, kwargs = self.deferred_messages.popleft()
            getattr(self.real_logger, level)(msg, *args, **kwargs)

    def _log(self, level, msg, *args, **kwargs):
        if self.is_real_logger_set:
            getattr(self.real_logger, level)(msg, *args, **kwargs)
        else:
            logging.getLogger(self.name).debug(f"Deferred message: {msg}")
            self.deferred_messages.append((level, msg, args, kwargs))

    def debug(self, msg, *args, **kwargs):
        self._log('debug', msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log('info', msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log('warning', msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log('error', msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log('critical', msg, *args, **kwargs)


def deferred_logger_test():
    # Usage
    logger = DeferredLogger('my_logger')

    # These messages will be stored
    logger.info("This is an early info message")
    logger.error("This is an early error message")

    # Later, when you set up your logging
    logging.basicConfig(level=logging.INFO)

    # The real logger is now set, and deferred messages are forwarded
    logger.warning("This is a new warning message")

    # You can also manually set the real logger if needed
    # custom_logger = logging.getLogger('custom')
    # logger.set_real_logger(custom_logger)
