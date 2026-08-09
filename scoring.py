from schedule import Schedule
from event import Event
from constraints import validate_placement, get_end_slot
from time_rep import weekly_slots, daily_slots, to_slot, slots_per_hour, slot_minutes


class ScoreBreakdown:
    def __init__ (self, total:int, components:dict):
        self.total = total
        self.components = components

class ScheduleScoringError(Exception):
    pass

class Judge:

    def score (self,schedule:Schedule, external_event_list:set[Event]):
        

        internal_event_list = {event for event in schedule.placements.keys()}

        # for placements in schedule.placements.values():
        #     for placement in placements:
        #         check = validate_placement(placement.event,schedule,placement.start)
        #         if not check["valid"]:
        #             raise ScheduleScoringError("Invalid schedules cannot be scored.")
            
        components = {
            "required_event" : self.has_req_events(external_event_list, internal_event_list),
            "occurances" : self.has_all_occurances(schedule),
            "optional_events": self.has_optional_events(external_event_list,internal_event_list),
            "pref_time": self.on_pref_time(schedule),
            "pref_gap": self.has_pref_gap(schedule)
        }

        weighted_method = ["optional_events","pref_time","pref_gap"]
        if external_event_list == internal_event_list:
            for component,result in components.items():
                if component in weighted_method:
                    components[component]=self.priority_weighting(result)

        for component,result in components.items():
            if component in weighted_method and isinstance(result,dict):
                components[component]=sum(result.values())

        return ScoreBreakdown(sum(components.values()), components)
            

    def has_req_events(self, external_event_list:set[Event],internal_event_list:set[Event]):
        internal_req_events = {event for event in internal_event_list if event.hard_flag}
        external_req_events = {event for event in external_event_list if event.hard_flag}
        if not len(external_req_events):
            return 1
        return len(external_req_events.intersection(internal_req_events))/len(external_req_events)

    def has_all_occurances(self, schedule: Schedule):
        occurance_satified = 0

        if not schedule.placements:
            return 1

        for event,placements in schedule.placements.items():
                freq = len(placements)

                if event.freq < 0:
                    raise ScheduleScoringError(f"Event frequency for {event.name} was set below 0")
                if freq > event.freq:
                    raise ScheduleScoringError(f"Placements ({freq}) surpassed the requested event frequency ({event.freq}) for {event.name}")
                
                try:
                    occurance_satified += freq/event.freq
                except ZeroDivisionError:
                    raise ScheduleScoringError(f"Event frequency for {event.name} was set to 0")
                
                
        return occurance_satified/len(schedule.placements.keys())

    def priority_weighting (self, value_dict: dict):
        if not isinstance(value_dict,dict):
            return value_dict
        
        weighted_value_dict = value_dict.copy()

        for priority,value in weighted_value_dict.items():
            weighted_value_dict[priority] = value * (priority+1)/6

        return weighted_value_dict

    # soft checks

    def has_optional_events(self, external_event_list:set[Event],internal_event_list:set[Event]):
        internal_optional_events = {event for event in internal_event_list if not event.hard_flag}
        external_optional_events = {event for event in external_event_list if not event.hard_flag}

        if not len(external_optional_events):
            return 1
        
        value_dict = dict()
        for event in internal_optional_events.intersection(external_optional_events):
            value_dict[event.priority]=1
        
        return value_dict

    def on_pref_time(self, schedule:Schedule):
        if not len(schedule.placements.values()):
            return 1
        
        value_dict = dict()
        for placements in schedule.placements.values():
            for placement in placements:
                soft_slots = []

                if not placement.event.preferred_start:
                    value_dict[placement.event.priority] = 1
                    continue

                for time in placement.event.preferred_start:
                    pref_slot = to_slot(time[0],time[1]//100,time[1]%100)
                    soft_slots.append(pref_slot)

                value = min(abs(placement.start-pref_slot) for pref_slot in soft_slots)
                value_dict[placement.event.priority] = weekly_slots/(value**2.46 + weekly_slots)

        return value_dict

    def has_pref_gap(self, schedule:Schedule):
        if not len(schedule.placements.values()):
            return 1
        
        value_dict = dict()
        for event,placements in schedule.placements.items():
            sorted_placements =sorted(placements, key=lambda placement: placement.start)

            for i in range(len(sorted_placements )):
                if i == len(sorted_placements )-1:
                    break

                else:
                    value_dict[event.priority]=(
                        4/
                        (abs(
                        abs(sorted_placements [i].start-sorted_placements [i+1].start)//96
                        - event.pref_gap_days
                        )**1.5
                        +4)
                    )

        return value_dict



        