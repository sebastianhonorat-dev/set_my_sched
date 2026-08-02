from time_rep import weekly_slots, daily_slots, to_slot
from event import Event
from schedule import Schedule

class ConstraintResult:

    def __init__(self,passed:bool, reasons:list):
        self.passed = passed
        self.reasons = reasons

def can_place (event: Event, schedule:Schedule, start_slot: int):
    reasons_list = []
    end_slot = start_slot + event.duration - 1

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
        end_slot = to_slot(time[0],time[2]//100,time[2]%100)-event.duration
        hard_slots.extend(range(first_slot,end_slot+1))


    end_slot = start_slot + event.duration - 1

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

    for time in hard_slots:
        if schedule.slots[time] is not None and schedule.slots[time].event_id == event.event_id:
            if abs(start_slot - time) < event.min_gap_days*daily_slots:
                reasons_list.append(f"Next event is below the minimum requested day gap.")
                break

    passed = len(reasons_list)==0

    return ConstraintResult(passed, reasons_list) 

def soft_check (event: Event, schedule:Schedule, start_slot: int):
    reasons = []
    soft_slots = []

    for time in event.preferred_start:
        first_slot = to_slot(time[0],time[1]//100,time[1]%100)
        end_slot = first_slot+event.duration -1
        soft_slots.extend(range(first_slot,end_slot))

    if start_slot not in soft_slots:
        reasons.append(f"Start time is not one of the preffered start times {event.preferred_start}") 
        if event.priority > 8:
            reasons.append(f"High priority event outside one of the preffered start times {event.preferred_start}")

    for time in soft_slots:
            if schedule.slots[time] is not None and schedule.slots[time].event_id == event.event_id:
                if abs(start_slot - time) < event.pref_gap_days*daily_slots:
                    reasons.append(f"Next event is below the preffered requested day gap.")
                    break

    for time in event.time_window:
        first_slot = to_slot(time[0],20,00)
        end_slot = to_slot(time[0]+1,5,00)
        if start_slot in range(first_slot,end_slot+1):
            reasons.append(f"Event doesn't avoid late night.")

    passed = len(reasons)==0
    
    return ConstraintResult(passed, reasons)

def validate_placement (event: Event, schedule:Schedule, start_slot: int):
    hard_check_results = hard_check(event, schedule, start_slot)
    soft_check_results = soft_check(event, schedule, start_slot)

    return {
        "valid":hard_check_results.passed,
        "hard_failures":hard_check_results.reasons,
        "soft_failures":soft_check_results.reasons
    }