from time_rep import weekly_slots
from event import Event
class Placement:
    _next_placement_id = 100

    def __init__(self, event: Event,start, end):
        self.placement_id = Placement._next_placement_id
        Placement._next_placement_id+=1

        self.event_id = event.id,
        self.name = event.name,
        self.start = start,
        self.end = end,
        self.duration = event.duration,
        self.freq = event.freq

class Schedule:

    def __init__(self, weekly_slots):
        self.slots = [None]*weekly_slots

    def create_placement (event:Event, start:int, end:int):
        return Placement(event, start, end)
    
    def place(self, placement: Placement):
        if placement.start <= 0 or placement.start > weekly_slots:
            # raise ValueError(f"Start time must be between 0 and {weekly_slots - 1}")
            return False
        if placement.end <= 0 or placement.end > weekly_slots:
            # raise ValueError(f"End time must be between 0 and {weekly_slots - 1}")
            return False
        if self.slots[placement.start] == True or self.slots[ placement.end] == True:
            # raise ValueError("Slot is not available")
            return False
        
        for slot in range(placement.start, placement.end+1):
            self.slots[slot] = placement
        return True

    def remove(self, placement: Placement):
        if placement.placement_id in self.slots:
            slot = self.slots.index(placement.placement_id)
            self.slots[slot]=None
            self.remove(placement)
            # for slot in self.slots:
            #     if slot == placement.placement_id:
            #         slot = None
            return True
        else:
            return False
    
    def move(self, placement: Placement, new_start, new_end):
        old_start, old_end = placement.start, placement.end

        self.remove(placement)
        placement.start, placement.end = new_start, new_end

        if not self.place(placement):
            placement.start, placement.end = old_start, old_end
            self.place(placement)
            return False
        
        return True
    
    def has_conflict(self, placement:Placement):
        events=set()
        placements=set()
        
        for slot in range(placement.start, placement.end+1):
            if self.slots[slot] is type(Placement):
                placements.add(slot.placement_id)
                events.add(slot.name)
                return tuple(placements,events)
            
        return False
    
    def find_free_time(self):
        free_time = []
        start_slot = -1

        for i in range(weekly_slots):

            if self.slots[i] is None:
                if start_slot < 0:
                    start_slot = i

            if self.slots[i] is type(Placement):
                if start_slot >= 0:
                    free_time.append([start_slot, i-1])
                    start_slot = -1
            
            if i == weekly_slots-1:
                if start_slot >= 0:
                    free_time.append([start_slot, i])
                    start_slot = -1
        return free_time