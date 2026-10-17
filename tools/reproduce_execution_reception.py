"""Replay TITAN-10B's native missed reception and receiver-only recovery.

Run from a complete git checkout:
    python tools/reproduce_execution_reception.py --out work/reception-replay

Uses public observations, unchanged v9.1 until tick 1497, and the native 20 ms
deadline. This diagnostic is not a match-strength benchmark. No automatic
retries hide interruptions; a failed run retains its raw record.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'student-sdk'))
from soccer import PlayerAction, play_match


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(c, obs, action, before):
    return {
        'tick': obs.tick, 'score': list(obs.score),
        'ball': [*obs.ball.position, *obs.ball.velocity],
        'last_touch': obs.ball.last_touch, 'holder': obs.ball.controlling_player,
        'friends': [[p.id, *p.position, *p.velocity] for p in obs.my_players],
        'opponents': [[p.id, *p.position, *p.velocity] for p in obs.opponents],
        'friend_cooldowns': {p.id: p.kick_cooldown_ticks for p in obs.my_players},
        'enemy_cooldowns': {p.id: p.kick_cooldown_ticks for p in obs.opponents},
        'actions': {k: v.as_dict() for k, v in action.players.items()},
        'plan_before': before, 'plan_after': c._receive_plan,
        'bank': c._bank_receive, 'chaser': c._chaser,
        'cover': c._cover_id, 'shape_cover': c._shape_cover_id,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Use a new output directory; preserve previous runs.')
    args.out.mkdir(parents=True)
    fixture = json.loads((ROOT / 'tests/fixtures/execution-reception-cases.json').read_text())
    expected = fixture['cases'][0]
    champion_path = ROOT / 'champions/v9.1/team.py'
    assert hashlib.sha256(champion_path.read_bytes()).hexdigest() == fixture['champion_sha256']
    # Preserve the exact historical opponent without changing the checkout.
    opponent = subprocess.check_output(
        ['git', 'show', '0476df9:my-team/team.py'], cwd=ROOT)
    assert hashlib.sha256(opponent).hexdigest() == '3aa39c8655e423490d6ce4027b0aadb49af9868379f4825ecbb66bf1ae658eaf'
    opponent_path = args.out.resolve() / 'v7/team.py'
    opponent_path.parent.mkdir()
    opponent_path.write_bytes(opponent)
    champion = load('reception_v91', champion_path)
    challenger = load('reception_execution', ROOT / 'experiments/titan-10b/team.py')

    class Replay(champion.Guardiola2011):
        def reset(self, seed):
            super().reset(seed)
            self.rows, self.aim, self.collected = [], None, None

        def act(self, obs):
            before = self._receive_plan
            action = super().act(obs)
            if self.recover and obs.tick == 1497:
                helper = challenger.Guardiola2011()
                helper._setup(obs.field)
                helper._friend_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.my_players}
                helper._enemy_cooldowns = {p.id: p.kick_cooldown_ticks for p in obs.opponents}
                passer = next(p for p in obs.my_players if p.id == 1)
                receiver = next(p for p in obs.my_players if p.id == 2)
                command = action.players[1]
                velocity = helper._requested_velocity(*obs.ball.velocity,
                                                     (command.kick_direction, command.kick_power))
                launch = helper._carrier_contact((1, *passer.position, *passer.velocity),
                                                 *obs.ball.position, *velocity, command.movement)
                path = helper._pass_path(launch, tuple(obs.ball.position), 2.6)
                route = helper._receiver_route((2, *receiver.position, *receiver.velocity), path,
                    [(p.id, *p.position, *p.velocity) for p in obs.opponents], .05, 2.6)
                assert route is not None
                self.aim = route[2]
            if self.recover and 1497 <= obs.tick <= 1510:
                if obs.ball.last_touch == 2 and self.collected is None:
                    self.collected = obs.tick
                if self.collected is None and action.players[2].kick_direction is None:
                    p = next(p for p in obs.my_players if p.id == 2)
                    action.set(2, PlayerAction(movement=self._move((2, *p.position, *p.velocity), self.aim)))
            if 1497 <= obs.tick <= 1497 + len(expected['trace']):
                self.rows.append(snapshot(self, obs, action, before))
            return action

    for recovery in (False, True):
        controller = Replay()
        controller.recover = recovery
        result = play_match(controller, str(opponent_path), seed=1239849544,
            kickoff_team=0, config_path=str(ROOT / 'configs/default.toml'),
            max_ticks=2400, per_decision_timeout_ms=20.).result
        record = {'result': result, 'frames': controller.rows,
                  'receiver_only_recovery': recovery, 'collection_tick': controller.collected}
        label = 'receiver-only-recovery' if recovery else 'champion-miss'
        (args.out / (label + '.json')).write_text(json.dumps(record, indent=2) + '\n')
        assert all(s['policy_errors'] == s['policy_timeouts'] == 0 for s in result['stats']), record['result']
        if recovery:
            assert controller.collected == 1507, controller.collected
        else:
            actual = json.loads(json.dumps(controller.rows))
            assert actual == [expected['start'], *expected['trace']], 'Native frame/action mismatch'
        print(label, 'verified; zero errors/timeouts', flush=True)


if __name__ == '__main__':
    main()
