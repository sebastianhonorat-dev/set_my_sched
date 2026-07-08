days_per_week = 7
hours_per_day = 24
min_per_hour = 60

slot_minutes = 15
slots_per_hour = min_per_hour // slot_minutes
daily_slots = hours_per_day * slots_per_hour
weekly_slots = days_per_week * daily_slots

days={
    0:"Monday",
    1:"Tuesday",
    2:"Wednesday",
    3:"Thursday",
    4:"Friday",
    5:"Saturday",
    6:"Sunday"
}


def to_slot(day, hour, minute):
    if type(day) is not int:
        raise TypeError("Day must be integer")
    if type(hour) is not int:
        raise TypeError("Hour must be integer")
    if type(minute) is not int:
        raise TypeError("Minute must be integer")

    if day not in range(days_per_week):
        raise ValueError("Day must be between 0-6")
    if hour not in range(hours_per_day):
        raise ValueError("Hour must be between 0-23")
    if minute not in range(min_per_hour):
        raise ValueError("Minute must be between 0-59")
    

    
    return (day * daily_slots) + (hour * slots_per_hour) + (minute//slot_minutes)
    
    
def from_slot(time_slot:int):
    if type(time_slot) is not int:
        raise TypeError("Time slot must be integer")
    
    if time_slot not in range(weekly_slots):
        raise ValueError("Time slot must be between 0-671")
    
    day = time_slot // daily_slots
    hour = (time_slot % daily_slots)// slots_per_hour
    min = ((time_slot % daily_slots) % slots_per_hour) * slot_minutes
    return day, hour, min


### TESTING ###

# schedule =  list(range(weekly_slot))

# first = 0
# last = len(schedule)//days_per_week

# for day in range(days_per_week):
#     print(f"{days[day]}:{schedule[first:last]}\n")

#     first, last = first + 96, last + 96

# print(to_slot(0,10,30))
# print(from_slot(383))
# print(from_slot(to_slot(6,0,30)))


# for slot in range(8):
#     print(slot, from_slot(slot), to_slot(*from_slot(slot)))

# print(to_slot(0,0,59),to_slot(0,0,45),from_slot(to_slot(0, 0, 59)))