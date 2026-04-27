class Skill:
    name = "base"

    def can_handle(self, intent: str) -> bool:
        return False

    def handle(self, command, context):
        raise NotImplementedError
