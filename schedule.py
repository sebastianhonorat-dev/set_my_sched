from time_rep import weekly_slots
from event import Event

class Placement:
    _next_placement_id = 100

    def __init__(self, event: Event, start:int):
        end = start+event.duration -1

        if start > end:
            raise ValueError("The start value must be less than end value")

        self.placement_id = Placement._next_placement_id
        Placement._next_placement_id+=1

        self.event = event
        self.start = start
        self.end = end
        self.duration = event.duration
        self.freq = event.freq

    def copy(self):
        copied = Placement.__new__(Placement)

        copied.placement_id = self.placement_id
        copied.event = self.event
        copied.start = self.start
        copied.end = self.end
        copied.duration = self.duration
        copied.freq = self.freq

        return copied
    
    def __eq__(self, other: "Placement"):
        if not isinstance(other, Placement):
            return NotImplemented

        return (
            self.event == other.event
            and self.start == other.start
            and self.end == other.end
        )

class Schedule:

    def __init__(self, total_slots=weekly_slots):
        self.slots = [None]*total_slots
        self.placements = {}
    
    def place(self, placement: Placement):
        placed = False

        if placement.start < 0 or placement.start >= weekly_slots:
            # raise ValueError(f"Start time must be between 0 and {weekly_slots - 1}")
            return placed
        if placement.end < 0 or placement.end >= weekly_slots:
            # raise ValueError(f"End time must be between 0 and {weekly_slots - 1}")
            return placed
        if self.slots[placement.start]:
            # raise ValueError("Slot is not available")
            return placed
        
        for slot in range(placement.start, placement.end+1):
            if self.slots[slot] is not None:
                self.remove(placement)
                placed = False
                break

            self.slots[slot] = placement

            placed = True

        if placed:
            if placement.event in self.placements:
                self.placements[placement.event].append(placement)
            else:
                self.placements[placement.event]=[placement]

        return placed


    def remove(self, placement: Placement):
        removed = False

        if placement in self.slots:

            for i in range(placement.start, placement.end+1):
                if self.slots[i] is placement:
                    self.slots[i] = None

                    removed= True

        if (placement.event in self.placements
        and placement in self.placements[placement.event]):
            
            if removed:
                placements = self.placements[placement.event]
                self.placements[placement.event]=placements.remove(placement)

            if not self.placements[placement.event]:
                del self.placements[placement.event]

        return removed
    
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
        conflict = False
        events=set()
        placements=set()
        
        for slot in range(placement.start, placement.end+1):
            if isinstance(self.slots[slot],(Placement)):
                existing_slot = self.slots[slot]
                placements.add(existing_slot.placement_id)
                events.add(existing_slot.name)
                conflict = True

        return conflict

    def get_conflicts(self, placement:Placement):
        events=set()
        placements=set()
        
        for slot in range(placement.start, placement.end+1):
            if isinstance(self.slots[slot],(Placement)):
                existing_slot = self.slots[slot]
                placements.add(existing_slot.placement_id)
                events.add(existing_slot.name)
        return placements,events
            
    def find_free_time(self):
        free_time = []
        start_slot = -1

        for i in range(weekly_slots):

            if self.slots[i] is None:
                if start_slot < 0:
                    start_slot = i

            if isinstance(self.slots[i],Placement):
                if start_slot >= 0:
                    free_time.append([start_slot, i-1])
                    start_slot = -1
            
            if i == weekly_slots-1:
                if start_slot >= 0:
                    free_time.append([start_slot, i])
                    start_slot = -1

        return free_time
    
    def event_lookup(self, event: Event):
        return len([
            placements for dict_event,placements in self.placements.items()
            if event == dict_event
        ])

    def frequency_satisfied(self, event: Event):
        return len(self.event_lookup(event)) == event.freq
    
    def slots_occupied(self):
        return sum(isinstance(slot, Placement) for slot in self.slots)
    
    def slots_free(self):
        return sum(not isinstance(slot, Placement) for slot in self.slots)

    def occupancy(self):
        return self.slots_occupied()/len(self.slots)
                
    def num_events(self):
        event_num = len({
            slot.event_id
            for slot in self.slots
            if slot is not None
        })

        return event_num
    
    def copy(self):
        copied_schedule = Schedule(len(self.slots))
        copied_placements = {}
        placement_copies = {}

        for i, placement in enumerate(self.slots):
            if placement is None:
                continue

            event = placement.event

            # Copy this Placement only once
            if id(placement) not in placement_copies:
                copied_placement = placement.copy()
                placement_copies[id(placement)] = copied_placement

                if event not in copied_placements:
                    copied_placements[event] = []

                copied_placements[event].append(copied_placement)

            # Reuse the same copied Placement for every slot it occupies
            copied_schedule.slots[i] = placement_copies[id(placement)]

        copied_schedule.placements = copied_placements

        return copied_schedule
    
    def __eq__(self, other: "Schedule"):
        if not isinstance(other, Schedule):
            return NotImplemented

        return self.slots == other.slots