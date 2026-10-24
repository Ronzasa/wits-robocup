import importlib.util, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "harness"))
import common; from common import soccer
sp = importlib.util.spec_from_file_location("c", os.path.join(HERE, "..", "candidates", "wedge_v1.py")); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
cls = [v for v in vars(m).values() if isinstance(v, type) and hasattr(v, "_wall_break")][0]
LOG = []
class T(cls):
    def _wall_break(self, obs, actions):
        before = {p.id: actions.players[p.id].kick_direction for p in obs.my_players}
        super()._wall_break(obs, actions)
        for p in obs.my_players:
            a = actions.players[p.id]
            if a.kick_direction != before[p.id] and obs.can_kick(p.id):
                LOG.append(("SHOT", obs.tick, tuple(round(x,1) for x in obs.ball.position), tuple(round(x,2) for x in a.kick_direction), sorted(round(q.position[1],1) for q in obs.opponents if abs(q.position[0]-obs.opponent_goal[0])<=3)))
        if LOG and obs.tick - LOG[-1][1] in (3, 6, 10): LOG.append(("  ball+%d" % (obs.tick - LOG[-1][1]), obs.tick, tuple(round(x,1) for x in obs.ball.position)))
soccer.play_match(T(), common.spec("bus_wall"), seed=30000, kickoff_team=0, max_ticks=1500)
for l in LOG[:40]: print(l)
