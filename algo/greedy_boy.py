from constraints import can_place, validate_placement
from event import Event
from schedule import Schedule, Placement
from time_rep import to_slot, weekly_slots
from scoring import Judge
from pathlib import Path
import time

class PlacementResults:

    def __init__(self,status:str|bool, event_id:str, event_name:str, reasons:list):
        self.status = status
        self.event_id = event_id
        self.event_name = event_name
        self.reasons = reasons

class GeneratorResults:

    def __init__(self,status:str|bool, schedule: Schedule,  algo_name:str, runtime:float, reasons:list):
        self.status = status
        self.schedule = schedule
        self.algo_name = algo_name
        self.runtime = runtime
        self.reasons = reasons

class GreedyScheduler:

    def __init__(self, schedule:Schedule, events: list[Event]):
        self.events = events
        self.schedule = schedule
        self.SimonCowell=Judge()

    def return_candidate_slots(self, event:Event):
        candidate_slot = []

        hard_starts = []
        for time in event.time_window:
            first_slot = to_slot(time[0],time[1]//100,time[1]%100)
            end_slot = to_slot(time[0],time[2]//100,time[2]%100)
            hard_starts.extend(range(first_slot,end_slot-event.duration+1))
            
        for slot in hard_starts:
            result=validate_placement(event, self.schedule, slot)
            if result["valid"]:
                candidate_slot.append(slot)

        return self.return_rank_candidates(event,candidate_slot)

    def return_rank_candidates(self,event:Event, candidate_slot:list):
        ranked_slots = dict()

        for slot in candidate_slot:
            placement = Placement(event,slot)
            temp_sched = self.schedule.copy()
            temp_sched.place(placement)
            score = self.SimonCowell.score(temp_sched,self.events)

            #placement is a slot or number, not an actual Placement object
            ranked_slots[slot] = score.total

        ranked_slots=dict(sorted(ranked_slots.items(), key=lambda x: x[1], reverse=True))

        return ranked_slots

    def place(self,event:Event):
        placed_all = "fail"
        failure_reasons=[]
        
        if not event.freq:
            failure_reasons.append(f"Event ({event.name}) frequency is missing")
            return PlacementResults(placed_all,event.event_id, event.name,failure_reasons)

        
        for occurance in range(event.freq):
            placed = False

            slots = self.return_candidate_slots(event)
            if not slots:
                failure_reasons.append(f"No slots are available for occurance {occurance+1}")
                break
            
            top_slot = list(slots.keys())[0]
            top_placement = Placement(event,top_slot)
            placed = self.schedule.place(top_placement)

            if not placed:
                failure_reasons.append(f"Occurance {occurance+1} failed to place")
                break

        if not failure_reasons:
            placed_all="success"

        elif failure_reasons and event in self.schedule.placements:
            removed = self.remove(event)
            if removed.status in ("fail","empty"):
                placed_all="corrupt"
                failure_reasons.extend(removed.reasons.failure_reasons)
              
        return PlacementResults(placed_all,event.event_id, event.name,failure_reasons)

    def remove(self, event:Event):
        removed_all = "fail"
        failure_reasons=[]

        if event not in self.schedule.placements.keys():
            failure_reasons.append(f"Event ({event.name}) not in schedule placements")
            removed_all = "empty"
            return PlacementResults(removed_all,event.event_id, event.name,failure_reasons)

        placements = self.schedule.placements[event].copy()
        for placement in placements:
            removed=False
            removed=self.schedule.remove(placement)

            if not removed:
                failure_reasons.append(f"Placement {placement.placement_id} for event {event.name} failed to remove")

        if not failure_reasons:
            removed_all = "success"

        return PlacementResults(removed_all,event.event_id, event.name,failure_reasons)

    def generate(self):
        start = time.perf_counter()

        failure_reasons = []
        priority_sort_events = sorted(self.events, key=lambda x:x.priority, reverse=True)
        event_scheduled = 0 
        event_failed = 0
        completed = True
        status = "success"

        for event in priority_sort_events:
            result = self.place(event)

            if result.status == "corrupt":
                completed = False
                failure_reasons.append(f"Schedule corrupted during {event.name} placement")
                failure_reasons.extend(result.reasons)
                break
            if result.status == "fail" and event.hard_flag:
                event_failed +=1
                completed = False
                failure_reasons.append(f"Failed to place required event {event.name}")
                failure_reasons.extend(result.reasons)
                break

            if result.status == "fail":
                failure_reasons.append(f"Failed to place optional event {event.name}")
                failure_reasons.extend(result.reasons)                
                event_failed +=1
            else:
                event_scheduled += 1

        end = time.perf_counter()

        cwd = Path(__file__).parents[1]
        report_dir = cwd/"docs"/"benchmark_reports"/"greedy_report.txt"
        report_dir.parent.mkdir(parents=True,exist_ok=True)
        with open(report_dir, "w") as file:
            file.write(
                f"""
                Schedule completed: {completed}
                Runtime: {end-start} sec
                Events provided: {len(self.events)}
                Events scheduled: {event_scheduled}
                Events failed: {event_failed}
                Required events completed: {len([event for event in self.schedule.placements.keys() if event.hard_flag])}
                Optional events completed: {len([event for event in self.schedule.placements.keys() if not event.hard_flag])}
                Occupancy: {len([slot for slot in self.schedule.slots if isinstance(slot, Placement)])/weekly_slots * 100:.2f}%
                Final schedule score: {self.SimonCowell.score(self.schedule, self.events).total}
            """
            )
        if failure_reasons and not completed:
            status = result.status
        return (GeneratorResults(status, self.schedule, "Greedy Algo", end-start,failure_reasons))