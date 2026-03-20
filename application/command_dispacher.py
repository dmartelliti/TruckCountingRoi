from application.handlers.base_handler import BaseHandler


class CommandDispatcher:

    def __init__(self, handlers: dict[type, BaseHandler]):
        self._handlers = handlers

    def dispatch(self, command):
        handler = self._handlers.get(type(command))

        if not handler:
            raise ValueError(f"No handler for {type(command)}")

        handler.handle(command)