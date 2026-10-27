"""Regression checks for league accounting and pairing. No matches are played."""
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import analyse
import bench
import workflow
import draw_workflow


def fixture(candidate="old", seed=1, side=0, kickoff=0, formation="custom", goals=(0, 0)):
    return {"candidate_key": "source:"+candidate, "candidate_spec": candidate+"/team.py",
            "opponent_key": "source:opponent", "opponent_spec": "opponent/team.py",
            "seed": seed, "candidate_side": side, "kickoff_team": kickoff,
            "formation": formation, "score": list(goals), "goal_difference": goals[0]-goals[1],
            "stats": [{}, {}], "ticks": 2400, "terminal_reason": "time_limit",
            "engine_version": bench._engine.ENGINE_VERSION, "config_hash": bench.CONFIG_HASH,
            "protocol_issues": [], "platform_error": None}


class AccountingTests(unittest.TestCase):
    def test_forfeits_override_a_leading_physical_score_on_both_sides(self):
        for side in (0, 1):
            for offender in (0, 1):
                with self.subTest(candidate_side=side, offender=offender):
                    row = fixture(side=side, goals=(4, 1))
                    row["terminal_reason"] = {"forfeit": {"team": offender}}
                    row["ticks"] = 70
                    original = copy.deepcopy(row)
                    expected = [0, 3] if offender == side else [3, 0]
                    expected_points = 0 if offender == side else 3
                    self.assertEqual(bench.score(row), expected)
                    self.assertEqual(analyse.score(row), expected)
                    self.assertEqual(bench.points(row), expected_points)
                    self.assertEqual(analyse.points(row), expected_points)
                    metrics = analyse.metrics([row])
                    summary = bench.summarise([row])
                    self.assertEqual(metrics["points"], expected_points)
                    self.assertEqual(metrics["goals"], expected)
                    self.assertEqual(summary["league_points"], expected_points)
                    self.assertEqual(summary["goals"], expected)
                    self.assertEqual(summary["team_a_wins"], int(offender != side))
                    self.assertEqual(summary["team_b_wins"], int(offender == side))
                    self.assertEqual(summary["forfeits"], 1)
                    self.assertEqual(summary["by_start"][f"side{side}-kickoff0"]["goals"], expected)
                    self.assertEqual(bench.check_row(row), [])
                    self.assertEqual(row, original, "Summaries must preserve raw evidence")

    def test_already_adjudicated_forfeit_is_idempotent(self):
        row = fixture(goals=(0, 3))
        row.update(terminal_reason={"forfeit": {"team": 0}}, on_field_score=[4, 1],
                   score_adjudication="course_forfeit_0_3")
        self.assertEqual(bench.score(row), [0, 3])
        self.assertEqual(analyse.score(row), [0, 3])
        self.assertEqual(bench.check_row(row), [])

    def test_platform_error_earns_no_draw_and_stays_in_denominator(self):
        draw = fixture()
        failure = fixture(seed=2)
        failure.update(score=None, ticks=0, platform_error="diagnostic failure",
                       protocol_issues=["platform_error"])
        for metrics in (analyse.metrics([draw, failure]), bench.summarise([draw, failure])):
            self.assertEqual(metrics["scheduled_matches"], 2)
            self.assertEqual(metrics["platform_errors"], 1)
            self.assertEqual(metrics["points_per_match"], 0.5)
        self.assertEqual(analyse.metrics([draw, failure])["wdl"], [0, 1, 0])
        self.assertEqual(bench.summarise([draw, failure])["draws"], 1)


class FormationTests(unittest.TestCase):
    def test_default_wrapper_forwards_lifecycle_but_suppresses_custom_formation(self):
        class Probe:
            name, version = "probe", "test"

            def __init__(self):
                self.events = []

            def initial_formation(self, field):
                raise AssertionError("Custom formation must not be requested")

            def reset(self, seed):
                self.events.append(("reset", seed))

            def act(self, obs):
                self.events.append(("act", obs))
                return action

            def on_match_end(self, result):
                self.events.append(("end", result))

        probe, observation, result, action = Probe(), object(), object(), object()
        with patch.object(bench, "load_controller", return_value=probe), \
                patch.object(bench, "baseline_names", return_value=("balanced",)):
            wrapped = bench.runtime_team("source.py", "default")
            self.assertIsInstance(wrapped, bench.DefaultFormation)
            self.assertIsNone(wrapped.initial_formation(object()))
            wrapped.reset(123)
            self.assertIs(wrapped.act(observation), action)
            wrapped.on_match_end(result)
            self.assertEqual(probe.events, [("reset", 123), ("act", observation), ("end", result)])
            self.assertEqual((wrapped.name, wrapped.version), (probe.name, probe.version))

    def test_custom_sources_and_native_baselines_are_forwarded_unchanged(self):
        with patch.object(bench, "load_controller", side_effect=AssertionError("Unexpected load")), \
                patch.object(bench, "baseline_names", return_value=("balanced",)):
            self.assertEqual(bench.runtime_team("source.py", "custom"), "source.py")
            self.assertEqual(bench.runtime_team("balanced", "default"), "balanced")

    def test_duplicate_keys_distinguish_formation_and_default_legacy_custom(self):
        custom, default = fixture(), fixture(formation="default")
        candidates = analyse.candidate_map([custom, default])
        self.assertEqual(len(candidates["source:old"]["rows"]), 2)
        with self.assertRaisesRegex(ValueError, "Duplicate fixture"):
            analyse.candidate_map([custom, copy.deepcopy(custom)])
        legacy = copy.deepcopy(custom)
        legacy.pop("formation")
        with self.assertRaisesRegex(ValueError, "Duplicate fixture"):
            analyse.candidate_map([custom, legacy])


class PairingTests(unittest.TestCase):
    def test_partial_comparison_uses_only_aligned_fixtures_and_discloses_unmatched(self):
        rows = [fixture(seed=1), fixture(seed=2, goals=(1, 0)),
                fixture("new", seed=1, goals=(1, 0)), fixture("new", seed=2),
                fixture("new", seed=3, goals=(8, 0))]
        result = analyse.paired(analyse.candidate_map(rows), "old/team.py", "new/team.py")
        self.assertEqual(result["matched_fixtures"], 2)
        self.assertEqual(result["seed_clusters"], 2)
        self.assertEqual(result["points_per_match_change"], 0)
        self.assertEqual((result["before_unmatched"], result["after_unmatched"]), (0, 1))
        self.assertFalse(result["complete_fixture_match"])

    def test_incompatible_formations_and_broken_matched_rows_are_rejected(self):
        old, new = fixture(), fixture("new", formation="default")
        with self.assertRaisesRegex(ValueError, "no matched fixtures"):
            analyse.paired(analyse.candidate_map([old, new]), "old/team.py", "new/team.py")
        new = fixture("new")
        new.update(score=None, platform_error="diagnostic failure", protocol_issues=["platform_error"])
        with self.assertRaisesRegex(ValueError, "platform/protocol failures"):
            analyse.paired(analyse.candidate_map([old, new]), "old/team.py", "new/team.py")

    def test_benchmark_comparison_refuses_formation_mismatch_and_incomplete_reports(self):
        def report(row):
            return {"teams": [{}], "results": [row], "valid_protocol": True, "complete": True}

        with tempfile.TemporaryDirectory(prefix="league-tools-") as directory:
            paths = [Path(directory)/"old.json", Path(directory)/"new.json"]
            old, new = report(fixture()), report(fixture("new", formation="default"))
            for path, content in zip(paths, (old, new)):
                path.write_text(json.dumps(content), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "formations"):
                bench.compare([str(path) for path in paths])
            new = report(fixture("new", goals=(1, 0)))
            paths[1].write_text(json.dumps(new), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.compare([str(path) for path in paths])
            compared = json.loads(output.getvalue())
            self.assertEqual(compared["matches"], 1)
            self.assertEqual(compared["points_per_match_change"], 2)
            new["complete"] = False
            paths[1].write_text(json.dumps(new), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incomplete protocol"):
                bench.compare([str(path) for path in paths])


class WorkflowTests(unittest.TestCase):
    def test_draw_conversion_requires_more_wins_without_points_regression(self):
        candidate = "new/team.py"
        rows = [fixture(draw_workflow.BASE, seed=seed, goals=(1, 0) if seed == 1 else (0, 0))
                for seed in range(1, 7)]
        # fixture() builds a convenience spec; use the actual workflow selector.
        for row in rows:
            row["candidate_spec"] = draw_workflow.BASE
        for seed in range(1, 7):
            row = fixture("new", seed=seed, goals=(1, 0) if seed <= 2 else (0, 1))
            row["candidate_spec"] = candidate
            rows.append(row)
        compared = draw_workflow.comparison(rows, candidate, 6, 6)
        self.assertEqual(compared["win_change"], 1)
        self.assertFalse(compared["qualifies"], "More wins must not excuse fewer league points")
        rows[8]["score"] = [1, 0]  # Three wins now exceed the control's eight points.
        self.assertTrue(draw_workflow.comparison(rows, candidate, 6, 6)["qualifies"])
        rows[8]["stats"][0]["validation"] = {"invalid_player_ids": 1}
        self.assertFalse(draw_workflow.comparison(rows, candidate, 6, 6)["qualifies"])

    def test_unavailable_kicks_are_reported_without_invalidating_legal_payloads(self):
        row = fixture()
        row["stats"][0]["validation"] = {"rejected_kicks": 49, "clamped_values": 1,
                                         "dropped_debug_payloads": 1}
        metrics = analyse.metrics([row])
        self.assertTrue(workflow.eligible_metrics(metrics))
        self.assertEqual(metrics["validation"]["rejected_kicks"], 49)
        for key in workflow.STRUCTURAL_ACTION_COUNTERS:
            invalid = copy.deepcopy(metrics)
            invalid["validation"][key] = 1
            self.assertFalse(workflow.eligible_metrics(invalid), key)
        self.assertEqual(metrics["validation"]["rejected_kicks"], 49)

    def test_count_refactor_preserves_the_original_declared_plan(self):
        if not workflow.PLAN.exists():
            self.skipTest("No original experiment plan exists in this checkout")
        original = workflow.read_json(workflow.PLAN)["model"]
        current = json.loads(json.dumps(workflow.plan_model()))
        self.assertEqual(current, original)
        self.assertEqual(workflow.fixture_count(workflow.SELECTION), 208)
        self.assertEqual(workflow.fixture_count(workflow.HOLDOUT), 520)
        self.assertEqual(workflow.fixture_count(workflow.HOLDOUT, "default"), 260)
        self.assertEqual(workflow.seed_count(workflow.HOLDOUT), 10)

    def test_release_changes_only_entry_metadata_with_unicode_and_crlf(self):
        source = ('"""A football policy: \u26bd."""\r\n'
                  'from soccer import TeamController\r\n'
                  'class Helper:\r\n    name = "helper"\r\n'
                  'class Policy(TeamController):\r\n'
                  '    name = "old"\r\n    version = "v0"\r\n'
                  '    def act(self, obs):\r\n        return obs\r\n').encode("utf-8")
        released = workflow.metadata_release(source, "release", "v1")
        expected = source.replace(b'name = "old"', b'name = "release"').replace(b'version = "v0"', b'version = "v1"')
        self.assertEqual(released, expected)
        self.assertIn(b'name = "helper"', released)

    def test_workflow_report_refuses_unadjudicated_forfeit_and_changed_raw_evidence(self):
        with tempfile.TemporaryDirectory(prefix="league-workflow-test-") as directory:
            folder = Path(directory)
            runtime = folder/"source.py"
            runtime.write_text("# immutable synthetic source\n", encoding="utf-8")
            sha = bench.digest(runtime)
            candidate = {"spec": "policy/team.py", "sha256": sha, "key": "source:"+sha}
            opponent = {"spec": "balanced", "sha256": None, "key": "baseline:balanced"}
            model = {"protocol": {"ticks": 2400, "players": 5, "timeout_ms": 20,
                                  "fixtures_per_seed_opponent": 4, "workers": 1},
                     "opponents": [opponent], "engine_version": bench._engine.ENGINE_VERSION,
                     "config_hash": bench.CONFIG_HASH, "infrastructure_sha256": {"test": "hash"}}
            rows = []
            for side in (0, 1):
                for kickoff in (0, 1):
                    row = fixture(side=side, kickoff=kickoff)
                    row.update(candidate_key=candidate["key"], candidate_spec=candidate["spec"],
                               opponent_key=opponent["key"], opponent_spec=opponent["spec"])
                    rows.append(row)
            rows[0].update(score=[4, 1], terminal_reason={"forfeit": {"team": 0}}, ticks=70)
            report = {"complete": True, "valid_protocol": True, "infrastructure_unchanged": True,
                      "source_snapshots_unchanged": True, "label": "synthetic", "seeds_exclusive": [1, 2],
                      "protocol": dict(model["protocol"], formation="custom"),
                      "engine_version": model["engine_version"], "config_hash": model["config_hash"],
                      "infrastructure_sha256": model["infrastructure_sha256"],
                      "teams": [{**candidate, "runtime_spec": str(runtime)}], "opponents": [opponent],
                      "results": rows}
            path = folder/"report.json"

            def save():
                path.write_text(json.dumps(report), encoding="utf-8")
                path.with_suffix(".jsonl").write_text("\n".join(json.dumps(row) for row in rows)+"\n", encoding="utf-8")

            save()
            with self.assertRaisesRegex(RuntimeError, "unadjudicated forfeit"):
                workflow.verify_report(path, ("synthetic", "custom", 1, 2), [candidate], model)
            rows[0]["score"] = [0, 3]
            save()
            checked = workflow.verify_report(path, ("synthetic", "custom", 1, 2), [candidate], model)
            self.assertEqual(bench.points(checked["results"][0]), 0)
            path.with_suffix(".jsonl").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Raw evidence differs"):
                workflow.verify_report(path, ("synthetic", "custom", 1, 2), [candidate], model)


class RayGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = bench.load_controller(str(workflow.HERE/"ray_cover/team.py"))
        cls.corrected = bench.load_controller(str(workflow.HERE/"ray_cover2/team.py"))
        cls.field = SimpleNamespace(simulation_hz=20, max_speed=8, acceleration=20,
            ball_friction=0.985, kick_impulse=22, kick_range=2.2, player_radius=1,
            ball_radius=0.45, my_goal=(-50, 0), opponent_goal=(50, 0), height=60,
            goal_width=14, centre_circle_radius=8)

    def targets(self, controller, bx, by, leading=True):
        controller.reset(0)
        controller.setup(self.field)
        requested = {}

        def capture(player, target):
            requested[player[0]] = target
            return (0, 0)

        controller.move = capture
        def player(index, x, y):
            return SimpleNamespace(id=index, position=(x, y), velocity=(0, 0), kick_cooldown_ticks=0)
        obs = SimpleNamespace(ball=SimpleNamespace(position=(bx, by), velocity=(0, 0)),
            my_players=[player(i, -48 if i < 4 else -10, y)
                        for i, y in enumerate((5.4, -1.8, 1.8, -5.4, 0))],
            opponents=[player(i, 35, (i-2)*5) for i in range(5)],
            score=(1, 0) if leading else (0, 0), can_kick=lambda _: False)
        controller.shell_act(obs, False)
        return [requested[i] for i in range(4)]

    def test_wide_ball_reproduces_old_overlap_and_corrected_spacing(self):
        old = sorted(target[1] for target in self.targets(self.original, -45.5, 21))
        fixed = sorted(target[1] for target in self.targets(self.corrected, -45.5, 21))
        self.assertEqual(old[-1], old[-2], "The archived defect must be reproduced")
        self.assertAlmostEqual(old[-1], 8.5)
        for a, b in zip(fixed, (2.02, 4.18, 6.34, 8.5)):
            self.assertAlmostEqual(a, b)

    def test_actual_guard_targets_stay_bounded_and_separated_across_pitch(self):
        for leading, depth in ((False, 1.2), (True, 3.3)):
            for distance in (depth+1.01, depth+2, 12, 24.99):
                for by in (-29, -21, -14, 0, 14, 21, 29):
                    with self.subTest(depth=depth, distance=distance, by=by):
                        targets = self.targets(self.corrected, -50+distance, by, leading)
                        ys = sorted(target[1] for target in targets)
                        self.assertTrue(all(abs(y) <= 8.5+1e-12 for y in ys))
                        self.assertTrue(all(b-a >= 2.16-1e-12 for a, b in zip(ys, ys[1:])))
                        self.assertTrue(all(abs(target[0]-(-50+depth)) < 1e-12 for target in targets))
        original = self.targets(self.original, -40, 0)
        corrected = self.targets(self.corrected, -40, 0)
        self.assertEqual(corrected, original, "A screen already inside its bounds must remain unchanged")


if __name__ == "__main__":
    unittest.main(verbosity=2)
