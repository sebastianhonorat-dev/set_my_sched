class Event:
    _next_id = 100

    def __init__(self,name, duration, freq, period, 
                 priority, time_window, 
                 preferred_start,hard_flag=True, 
                 min_gap_days=0, pref_gap_days = 0):

        #TypeErrors
        if type(name) is not str:
            raise TypeError("Name must be a string")
        
        if type(duration) is not int:
            raise TypeError("Duration must be integer.")
        
        if type(period) is not str:
            raise TypeError("Period must be string.")
        
        if type(freq) is not int:
            raise TypeError("Frequency must be integer.")
        
        if type(priority) is not int:
            raise TypeError("Priority must be integer.")
            
        if type(time_window) is not tuple:
            raise TypeError("Time window must be a nested tuple of integers.")
        for time_span in time_window:
            if type(time_span) is not tuple:
                raise TypeError("Each time span within the tuple must also be an tuple")
            if type(time_span[0]) is not int:
                raise TypeError("Each day within the tuple must be an integer")
            if type(time_span[1]) is not int or type(time_span[2] )is not int:
                raise TypeError("Each time within the nested tuples must be an integer")
            
        if type(preferred_start) is not tuple:
            raise TypeError("Preferred times must be a tuple of integer.")
        for time in preferred_start:
            if type(time) is not int:
                raise TypeError("Times within the tuple must be integer ")
            
        if type(hard_flag) is not bool:
            raise TypeError("Hard event flag must be boolean.")
        
        if type(min_gap_days) is not int:
            raise TypeError("Gap days must be integer.")
        
        if type(pref_gap_days) is not int:
            raise TypeError("Gap days must be integer.")
        
        #ValueErrors

        if duration < 1 or duration > 96:
            raise ValueError("Duration must between 1 and 96.")
        if period not in ("daily", "weekly"):
            raise ValueError("Period must be \"daily\" or \" weekly\".")
        
        if (period == "daily" and freq < 1 or 
            period == "daily" and freq > 96):
            raise ValueError("Frequency must between 1-96 when period is daily.")
        if  (period == "weekly" and freq < 1 or
            period == "weekly" and freq > 7):
            raise ValueError("Frequency must between 1-7 when period is weekly.")
        
        if priority < 0 or priority > 10:
            raise ValueError("Priority must between 0-10.")
        
        for time_span in time_window:
            if len(time_span) not in (0,3):
                raise ValueError("Time window must include a day and two (2) time slots or None")
            if len(time_span) == 0:
                continue
            if time_span[0] < 0 or time_span[0] > 6:
                raise ValueError("Days in the day window must be between 0-6")
            if (time_span[1] < 0 or time_span[1] > 2359 or
             time_span[2] < 0 or time_span[2] > 2359):
                raise ValueError("Time window values must be between 0000 and 2359")
        
        for time_span in preferred_start:
            if len(time_span) not in (0,2):
                raise ValueError("Time window must include a day and a starting time slots or None")
            if time_span[0] < 0 or time_span[0] > 6:
                raise ValueError("Day for the preferred start must be between 0 and 6")
            if time_span[1] < 0 or time_span[1] > 2359:
                raise ValueError("Time for the preferred start must be between 0000 and 2359")
        
        if min_gap_days < 0 or min_gap_days > 6:
            raise ValueError("Gap days must between 0-6.")
        
        if pref_gap_days < 0 or pref_gap_days > 6:
            raise ValueError("Gap days must be between 0-6.")


        self.event_id = Event._next_id
        Event._next_id += 1

        self.name = name
        self.duration = duration
        self.freq = freq
        self.period = period
        self.priority = priority
        self.hard_flag = hard_flag
        self.time_window = time_window
        self.preferred_start = preferred_start
        self.min_gap_days = min_gap_days
        self.pref_gap_days = pref_gap_days