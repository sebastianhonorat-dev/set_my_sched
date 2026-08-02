from time_rep import weekly_slots, daily_slots, to_slot, slots_per_hour, slot_minutes
from event import Event
from schedule import Schedule

class ConstraintResult:

    def __init__(self,passed:bool, reasons:list):
        self.passed = passed
        self.reasons = reasons

def can_place (event: Event, schedule:Schedule, start_slot: int):
    reasons_list = []
    end_slot = get_end_slot(event, start_slot)

    if start_slot < 0 or start_slot >= weekly_slots:
        # raise ValueError(f"Start time must be between 0 and {weekly_slots - 1}")
        reasons_list.append(f"Start time must be between 0 and {weekly_slots - 1}")
        
    if  end_slot >= weekly_slots:
        # raise ValueError(f"End time must be between 0 and {weekly_slots - 1}")
        reasons_list.append(f"End time must be between 0 and {weekly_slots - 1}")  


    if len(reasons_list)==0:
        for slot in schedule.slots[start_slot:end_slot+1]:
        
            if slot is not None:
                # raise ValueError("Slots are not available")
                reasons_list.append(f"Slots are not available")
                break

    passed = len(reasons_list)==0

    return ConstraintResult(passed, reasons_list) 

def hard_check (event: Event, schedule:Schedule, start_slot: int):
    reasons_list = []

    hard_slots = []
    for time in event.time_window:

        first_slot = to_slot(time[0],time[1]//100,time[1]%100)
        end_slot = get_end_slot(event,to_slot(time[0],time[2]//100,time[2]%100))
        hard_slots.extend(range(first_slot,end_slot+1))


    end_slot = get_end_slot(event, start_slot)

    if start_slot < 0 or start_slot >= weekly_slots:
        # raise ValueError(f"Start time must be between 0 and {weekly_slots - 1}")
        reasons_list.append(f"Start time must be between 0 and {weekly_slots - 1}")
        
    if  end_slot >= weekly_slots:
        # raise ValueError(f"End time must be between 0 and {weekly_slots - 1}")
        reasons_list.append(f"End time must be between 0 and {weekly_slots - 1}")  
    
    if start_slot not in hard_slots:
        reasons_list.append(f"Start time must be within hard time_window {event.day_window}")  

    if len(reasons_list)==0:
        for slot in schedule.slots[start_slot:end_slot+1]:
        
            if slot is not None:
                # raise ValueError("Slots are not available")
                reasons_list.append(f"Slots are not available")
                break

    freq = 0
    for placement in schedule.placements.values():
        if placement.event_id == event.event_id:
            freq +=1

        if freq == event.freq:
            reasons_list.append(f"Event's frequency has already been fulfilled")
            break

    gaps = check_gap(schedule, event, start_slot)
    for gap in gaps:
        if gap < event.min_gap_days:
            reasons_list.append(f"Next event is below the minimum gap days {event.min_gap_days}.")
            break

    passed = len(reasons_list)==0

    return ConstraintResult(passed, reasons_list) 

def soft_check (event: Event, schedule:Schedule, start_slot: int):
    reasons = []
    soft_slots = []

    for time in event.preferred_start:
        first_slot = to_slot(time[0],time[1]//100,time[1]%100)
        end_slot = get_end_slot(event,first_slot)
        soft_slots.extend(range(first_slot,end_slot))

    if start_slot not in soft_slots:
        reasons.append(f"Start time is not one of the preffered start times {event.preferred_start}") 
        if event.priority > 8:
            reasons.append(f"High priority event outside one of the preffered start times {event.preferred_start}")

    gaps = check_gap(schedule, event, start_slot)
    for gap in gaps:
        if gap < event.pref_gap_days:
            reasons.append(f"Gap between events is less then preffered gap {event.pref_gap_days}")
            break

    for time in event.time_window:
        first_slot = to_slot(time[0],19,00)
        end_slot = to_slot(time[0]+1,5,00)
        if start_slot in range(first_slot,end_slot+1):
            reasons.append(f"Event does not avoid late night.")

    passed = len(reasons)==0
    
    return ConstraintResult(passed, reasons)

def day_from_slot(time_slot:int):
    if type(time_slot) is not int:
        raise TypeError("Time slot must be integer")
    
    if time_slot not in range(weekly_slots):
        raise ValueError("Time slot must be within 0-671")
    
    day = time_slot // daily_slots
    return day

def time_from_slot(time_slot:int):
    if type(time_slot) is not int:
        raise TypeError("Time slot must be integer")
    
    if time_slot not in range(weekly_slots):
        raise ValueError("Time slot must be within 0-671")
    
    hour = (time_slot % daily_slots)// slots_per_hour
    min = ((time_slot % daily_slots) % slots_per_hour) * slot_minutes
    return hour*100+min

def get_end_slot(event: Event,start_slot:int):
    return start_slot + event.duration - 1

def cross_midnight(event:Event, start_slot):
    return (
        day_from_slot(start_slot) != 
        day_from_slot(start_slot+event.duration-1)
    )

def check_gap(schedule: Schedule, event: Event, start_slot:int):
    gap = []

    for placement in schedule.placements.values():
        if placement.event_id == event.event_id:
            gap.append(abs(placement.start - start_slot))

    return gap

def validate_placement (event: Event, schedule:Schedule, start_slot: int):
    hard_check_results = hard_check(event, schedule, start_slot)
    soft_check_results = soft_check(event, schedule, start_slot)

    return {
        "valid":hard_check_results.passed,
        "hard_failures":hard_check_results.reasons,
        "soft_failures":soft_check_results.reasons
    }