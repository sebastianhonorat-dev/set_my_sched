days_per_week = 7
hours_per_day = 24
min_per_hour = 60

slot_minutes = 15
slots_per_hour = min_per_hour // slot_minutes
daily_slots = hours_per_day * slots_per_hour
weekly_slot = days_per_week * daily_slots

days={
    0:"Monday",
    1:"Tuesday",
    2:"Wednesday",
    3:"Thursday",
    4:"Friday",
    5:"Saturday",
    6:"Sunday"
}



schedule =  list(range(weekly_slot))

first = 0
last = len(schedule)//days_per_week

for day in range(days_per_week):
    print(f"{days[day]}:{schedule[first:last]}\n")

    first, last = first + 96, last + 96

def to_slot(day, hour, min):
    if 0 > day > 6:
        raise ValueError("Day must be between 0-6")
    if 0 > hour > 23:
        raise ValueError("Hour must be between 0-23")
    if 0 > min > 59:
        raise ValueError("min must be between 0-59")

    return (day * daily_slots) + (hour * slots_per_hour) + (min_per_hour//min)

def from_slot(time_slot:int):
    if 0 > time_slot > 671:
        raise ValueError("Time slot must be between 0-671")
    
    day = time_slot // 96
    hour = (time_slot % 96)//4
    min = ((time_slot % 96) % 4) *15
    return day, hour, min


print(to_slot(0,10,30))
print(from_slot(383))
print(from_slot(to_slot(6,0,30)))
