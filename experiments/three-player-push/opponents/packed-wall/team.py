"""Independent public-observation packed wall with goalkeeper centred."""
import math
from soccer import TeamController,TeamAction,PlayerAction
class PackedWall(TeamController):
 name='Packed wall development opponent'
 version='1.0'
 def reset(self,seed):pass
 def act(self,obs):
  a=TeamAction();ys=(0.,-5.6,-2.8,2.8,5.6)
  for p in obs.my_players:
   dx=obs.my_goal[0]+obs.field.player_radius-p.position[0];dy=ys[p.id]-p.position[1]
   d=math.hypot(dx,dy);v=min(obs.field.max_speed,d*5)
   ux,uy=(dx/d,dy/d) if d>1e-9 else (0.,0.)
   ax=(ux*v-p.velocity[0]*.9)/(obs.field.acceleration/obs.field.simulation_hz)
   ay=(uy*v-p.velocity[1]*.9)/(obs.field.acceleration/obs.field.simulation_hz)
   norm=max(1.,math.hypot(ax,ay));move=(ax/norm,ay/norm)
   if obs.can_kick(p.id):a.set(p.id,PlayerAction(movement=move,kick_direction=(1.,0.),kick_power=1.))
   else:a.set(p.id,PlayerAction(movement=move))
  return a
