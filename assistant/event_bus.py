class EventBus:
    def __init__(self, callback=None):
        self.callback = callback

    def emit(self, event_type: str, message: str = "", data=None):
        if self.callback:
            self.callback(event_type, message, data or {})


class NullEventBus(EventBus):
    def __init__(self):
        super().__init__(callback=None)
