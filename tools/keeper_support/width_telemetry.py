"""Passive measurements from native observations, outside decision timing."""
from collections import Counter
import math

from keeper_support.telemetry import Telemetry as KeeperTelemetry


class Telemetry(KeeperTelemetry):
    def __init__(self):
        super().__init__()
        self.phases={name:Counter() for name in ('normal','moderate','ultra')}
        self.score=None

    def observe(self,obs,answer,controller=None):
        super().observe(obs,answer,controller)
        phase='normal' if obs.tick<obs.max_ticks//2 else (
            'ultra' if obs.max_ticks-obs.tick<=int(30*obs.field.simulation_hz) else 'moderate')
        counts=self.phases[phase]
        counts['ticks']+=1
        players=obs.my_players[1:]
        if players:
            counts['outfield_y_span_sum']+=max(p.position[1] for p in players)-min(p.position[1] for p in players)
        bx,by=obs.ball.position
        carrier=obs.ball.controlling_player
        if obs.ball.controlling_team==0 and carrier is not None:
            support=[p for p in players if p.id!=carrier]
            if support:
                counts['controlled_support_ticks']+=1
                counts['nearest_support_distance_sum']+=min(math.hypot(p.position[0]-bx,p.position[1]-by) for p in support)
        if self.score is not None:
            counts['goals_for']+=max(0,obs.score[0]-self.score[0])
            counts['goals_against']+=max(0,obs.score[1]-self.score[1])
        self.score=obs.score
        action,elapsed,error=answer
        if error is None and elapsed<20.:
            events=action.debug.get('titan_x',())
            counts['spacing_command_ticks']+=int('wide_support' in events or 'phase_support' in events)
            if action.debug.get('match_phase') is not None:
                counts['schedule_debug_ticks']+=1

    def result(self):
        result=super().result()
        result['phases']={name:dict(c) for name,c in self.phases.items()}
        result['phase_scope']='Clock phases, actual native outfield width and support distances. Command ticks are not executions; phase goals use observation-time score changes.'
        return result
