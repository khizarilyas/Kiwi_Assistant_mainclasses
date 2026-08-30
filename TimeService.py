from datetime import datetime

class TimeService:


    def get_time(self):

        time_now = datetime.now()
        hour = time_now.hour
        minute = time_now.minute

        if hour < 12:
            time_of_day = "AM"

        elif hour > 12 or hour == 12:
            time_of_day = "PM"

        # Convert into 12 hour as it is automatically 24 hour
        hour = hour % 12 or 12

        # Assistant will say 9 oh 5 instead of 9 5
        minute = f"oh {minute}" if minute < 10 else minute

        return f"It's {hour} {minute} {time_of_day}."





