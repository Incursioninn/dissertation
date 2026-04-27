from datetime import datetime, timedelta


class ReminderSkill:
    name = "reminders"

    def __init__(self):
        self.reminders = []

    def can_handle(self, intent: str):
        return intent == "set_reminder"

    def handle(self, command, context):
        minutes = command.entities.get("minutes")
        reminder_text = command.entities.get("reminder_text")

        if not minutes:
            return "Не понял, через сколько минут напомнить."

        when = datetime.now() + timedelta(minutes=minutes)
        self.reminders.append({
            "time": when,
            "text": reminder_text or "о вашей задаче",
            "done": False,
        })

        return f"Хорошо, напомню через {minutes} минут."

    def check(self, tts):
        now = datetime.now()
        for reminder in self.reminders:
            if not reminder["done"] and now >= reminder["time"]:
                tts.say(f"Напоминание: {reminder['text']}.")
                reminder["done"] = True
