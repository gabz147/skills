from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "arc_montage.py"
SPEC = importlib.util.spec_from_file_location("arc_montage", MODULE_PATH)
assert SPEC and SPEC.loader
arc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(arc)


class ArcMontageDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cfg = arc.normalize_config({"footage_path": self.temp.name, "output_path": self.temp.name})

    def frame(self, timestamp: float, *, bright: float = 0.0, blue: float = 0.0,
              red: float = 0.0, centroid=(160.0, 90.0), sparks: int = 0,
              status: float = .50, edge_red: float = 0.0) -> dict:
        return {
            "time": timestamp,
            "bright_score": bright,
            "bright_centroid": list(centroid) if bright else None,
            "bright_area": 12 if bright else 0,
            "blue_score": blue,
            "blue_centroid": list(centroid) if blue else None,
            "blue_area": 12 if blue else 0,
            "red_score": red,
            "red_centroid": list(centroid) if red else None,
            "red_area": 12 if red else 0,
            "spark_count": sparks,
            "status_fill": status,
            "edge_red": edge_red,
            "phash": "01" * 32,
        }

    def candidate(self) -> dict:
        return {
            "shot_times": [1.0], "first_shot_time": 1.0,
            "weapon": "EQUALIZER", "weapon_confidence": .85,
            "fire_confidence": .8, "ammo_changes": [.08],
            "ammo_change_kinds": ["stable_glyph_change"],
            "candidate_sources": ["ammo_hud"],
        }

    def knock_frames(self, *, far_flare: bool = False, player_damage: bool = False) -> list[dict]:
        flare_center = (230.0, 130.0) if far_flare else (162.0, 91.0)
        after_status = .30 if player_damage else .50
        edge = .05 if player_damage else 0.0
        return [
            self.frame(.95),
            self.frame(1.00),
            self.frame(1.10, bright=.55, blue=.35, sparks=3),
            self.frame(1.14, red=.38, centroid=flare_center, status=after_status, edge_red=edge),
            self.frame(1.18, red=.42, centroid=flare_center, status=after_status, edge_red=edge),
        ]

    def test_normalized_roi_pixels_scale_cleanly(self) -> None:
        roi = [.25, .25, .75, .75]
        self.assertEqual(arc.normalized_roi_to_pixels(1920, 1080, roi), (480, 270, 1440, 810))
        self.assertEqual(arc.normalized_roi_to_pixels(2560, 1440, roi), (640, 360, 1920, 1080))

    def test_config_rejects_invalid_roi_and_normalizes_weapons(self) -> None:
        cfg = arc.normalize_config({"footage_path": self.temp.name,
                                    "preferred_weapons": ["aphelion", "EQUALIZER", "aphelion"]})
        self.assertEqual(cfg["preferred_weapons"], ["APHELION", "EQUALIZER"])
        with self.assertRaises(ValueError):
            arc.normalize_config({"footage_path": self.temp.name, "hud_roi": [.9, .7, .8, 1]})

    def test_detector_signature_ignores_ranking_but_tracks_detector_inputs(self) -> None:
        original = arc.detector_signature(self.cfg)
        ranking_change = dict(self.cfg, preferred_weapons=["ANVIL"], event_priority=["shield_hit"])
        self.assertEqual(original, arc.detector_signature(ranking_change))
        detector_change = dict(self.cfg, reticle_roi=[.40, .30, .60, .70])
        self.assertNotEqual(original, arc.detector_signature(detector_change))

    def test_bundled_weapon_masks_are_distinct(self) -> None:
        templates = arc.load_weapon_templates()
        self.assertEqual(arc.recognize_weapon(templates["APHELION"], .42)[0], "APHELION")
        self.assertEqual(arc.recognize_weapon(templates["EQUALIZER"], .42)[0], "EQUALIZER")
        self.assertLess(arc.mask_similarity(templates["APHELION"], templates["EQUALIZER"]), .5)

    def test_ammo_glyph_changes_group_into_equalizer_burst(self) -> None:
        observations = []
        for timestamp, signature in ((0.0, 0), (.125, 0), (.250, 15), (.375, 15), (.500, 63), (.625, 63)):
            observations.append({"time": timestamp, "weapon": "EQUALIZER", "weapon_confidence": .8,
                                 "ammo_signature": signature, "ammo_signature_size": 16})
        bursts = arc.group_ammo_bursts(observations, self.cfg)
        self.assertEqual(len(bursts), 1)
        self.assertEqual(bursts[0]["weapon"], "EQUALIZER")
        self.assertEqual(bursts[0]["shot_times"], [.25, .5])

    def test_weapon_swap_does_not_seed_ammo_event(self) -> None:
        observations = [
            {"time": 0.0, "weapon": "APHELION", "weapon_confidence": .9,
             "ammo_signature": 0, "ammo_signature_size": 16},
            {"time": .125, "weapon": "EQUALIZER", "weapon_confidence": .9,
             "ammo_signature": 15, "ammo_signature_size": 16},
        ]
        self.assertEqual(arc.group_ammo_bursts(observations, self.cfg), [])

    def test_ordered_nearby_red_flare_classifies_knock(self) -> None:
        event = arc.classify_causal_sequence(self.knock_frames(), self.candidate(), self.cfg)
        self.assertIsNotNone(event)
        self.assertEqual(event["label"], "raider_knock_flare")
        self.assertEqual(event["tier"], "A")
        self.assertEqual(event["evidence"]["flare_frames"], 2)
        self.assertGreater(event["evidence"]["flare_time"], event["evidence"]["impact_time"])

    def test_far_red_effect_is_not_a_knock(self) -> None:
        event = arc.classify_causal_sequence(self.knock_frames(far_flare=True), self.candidate(), self.cfg)
        self.assertIsNotNone(event)
        self.assertEqual(event["label"], "shield_break")
        self.assertIsNone(event["evidence"]["flare_time"])

    def test_same_frame_red_is_not_later_flare(self) -> None:
        frames = [self.frame(.95), self.frame(1.0),
                  self.frame(1.1, bright=.55, blue=.35, red=.45, sparks=3),
                  self.frame(1.14)]
        event = arc.classify_causal_sequence(frames, self.candidate(), self.cfg)
        self.assertIsNotNone(event)
        self.assertNotEqual(event["label"], "raider_knock_flare")

    def test_player_damage_penalizes_but_does_not_erase_outgoing_knock(self) -> None:
        clean = arc.classify_causal_sequence(self.knock_frames(), self.candidate(), self.cfg)
        damaged = arc.classify_causal_sequence(self.knock_frames(player_damage=True), self.candidate(), self.cfg)
        self.assertEqual(damaged["label"], "raider_knock_flare")
        self.assertGreater(damaged["evidence"]["player_damage_confidence"], 0)
        self.assertLess(damaged["confidence"], clean["confidence"])

    def test_hud_sampling_uncertainty_allows_impact_before_observed_change(self) -> None:
        candidate = self.candidate()
        candidate["shot_time_uncertainty"] = .125
        frames = [self.frame(.84), self.frame(.90, bright=.50, blue=.30, sparks=2),
                  self.frame(.94, red=.35, centroid=(161, 90)),
                  self.frame(.98, red=.40, centroid=(161, 90)), self.frame(1.02)]
        event = arc.classify_causal_sequence(frames, candidate, self.cfg)
        self.assertIsNotNone(event)
        self.assertEqual(event["label"], "raider_knock_flare")
        self.assertLess(event["evidence"]["impact_time"], candidate["first_shot_time"])

    def test_bright_flare_does_not_replace_earlier_impact(self) -> None:
        frames = [self.frame(.95), self.frame(1.0),
                  self.frame(1.10, bright=.42, blue=.32, sparks=2),
                  self.frame(1.14, bright=.95, red=.88, centroid=(161, 90)),
                  self.frame(1.18, bright=.90, red=.92, centroid=(161, 90))]
        event = arc.classify_causal_sequence(frames, self.candidate(), self.cfg)
        self.assertEqual(event["label"], "raider_knock_flare")
        self.assertAlmostEqual(event["evidence"]["impact_time"], 1.10)

    def test_visual_fallback_knock_remains_review_only_tier_c(self) -> None:
        candidate = self.candidate()
        candidate.update({"weapon": None, "candidate_sources": ["visual_fallback"], "fire_confidence": .4})
        event = arc.classify_causal_sequence(self.knock_frames(), candidate, self.cfg)
        self.assertEqual(event["label"], "raider_knock_flare")
        self.assertEqual(event["tier"], "C")
        self.assertFalse(event["evidence"]["confirmed_fire"])

    def test_merge_preserves_overlapping_logical_seeds(self) -> None:
        left = {"start": 1.0, "end": 3.0, "first_shot_time": 1.4, "shot_times": [1.4],
                "weapon": "APHELION", "weapon_confidence": .8, "fire_confidence": .7,
                "ammo_changes": [.1], "ammo_change_kinds": ["stable_glyph_change"],
                "candidate_sources": ["ammo_hud"]}
        right = {**left, "start": 2.5, "end": 4.0, "first_shot_time": 2.7,
                 "shot_times": [2.7], "weapon": "EQUALIZER"}
        groups = arc.merge_candidate_windows([left, right], 10.0)
        self.assertEqual(len(groups), 1)
        self.assertEqual([seed["weapon"] for seed in groups[0]["seeds"]], ["APHELION", "EQUALIZER"])

    def test_anchor_jump_does_not_seed_ammo_change(self) -> None:
        observations = [
            {"time": 0.0, "weapon": "EQUALIZER", "weapon_confidence": .8,
             "weapon_peak_y": 80, "ammo_signature": 0, "ammo_signature_size": 16},
            {"time": .125, "weapon": "APHELION", "weapon_confidence": .8,
             "weapon_peak_y": 103, "ammo_signature": 15, "ammo_signature_size": 16},
        ]
        self.assertEqual(arc.group_ammo_bursts(observations, self.cfg), [])

    def test_aphelion_candidate_keeps_post_impact_flare_time(self) -> None:
        observations = []
        for timestamp, signature in ((0.0, 0), (.125, 0), (.25, 15), (.375, 15)):
            observations.append({"time": timestamp, "weapon": "APHELION", "weapon_confidence": .8,
                                 "weapon_peak_y": 103, "ammo_signature": signature, "ammo_signature_size": 16})
        burst = arc.group_ammo_bursts(observations, self.cfg)[0]
        self.assertGreaterEqual(burst["end"], burst["shot_times"][-1] + 3.0)

    def test_component_scoring_is_resolution_invariant(self) -> None:
        low = [{"area": 28, "centroid": [160, 90], "bbox": [153, 83, 167, 97]}]
        high = [{"area": 63, "centroid": [240, 135], "bbox": [230, 125, 251, 146]}]
        low_score = arc.component_summary(low, (160, 90), 46, 28)[0]
        high_score = arc.component_summary(high, (240, 135), 69, 63)[0]
        self.assertAlmostEqual(low_score, high_score, places=2)

    def test_tier_dominates_weapon_boost(self) -> None:
        events = [
            {"source": "a", "start": 0, "confidence": .60, "tier": "A",
             "label": "raider_knock_flare", "weapon": None},
            {"source": "b", "start": 0, "confidence": .95, "tier": "B",
             "label": "shield_break", "weapon": "EQUALIZER"},
        ]
        ranked = arc.rank_events(events, self.cfg)
        self.assertEqual(ranked[0]["label"], "raider_knock_flare")

    def test_deduplication_keeps_stable_unique_ids(self) -> None:
        common = {"source": "same.mp4", "source_hash": "abc", "source_fps": 60,
                  "end": 3.0, "confidence": .8, "label": "shield_break",
                  "evidence": {"peak_phash": "0" * 64}}
        first = {**common, "start": 0.0, "first_shot_time": 1.0, "event_time": 1.2}
        second = {**common, "start": 1.5, "first_shot_time": 2.0, "event_time": 2.2}
        first["id"], second["id"] = arc.stable_event_id(first), arc.stable_event_id(second)
        kept, groups = arc.deduplicate([first, second])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(groups), 1)
        self.assertNotEqual(groups[0]["event"], groups[0]["duplicate_of"])

    def test_distinct_knocks_survive_overlapping_edit_handles(self) -> None:
        common = {"source": "same.mp4", "source_hash": "abc", "source_fps": 60,
                  "confidence": .8, "label": "raider_knock_flare", "tier": "A",
                  "weapon": "EQUALIZER"}
        first = {**common, "start": 0.0, "end": 6.0, "first_shot_time": 1.0, "event_time": 1.2,
                 "evidence": {"peak_phash": "0" * 64}}
        second = {**common, "start": 3.0, "end": 9.0, "first_shot_time": 4.0, "event_time": 4.2,
                  "evidence": {"peak_phash": "1" * 64}}
        first["id"], second["id"] = arc.stable_event_id(first), arc.stable_event_id(second)
        kept, groups = arc.deduplicate([first, second])
        self.assertEqual(len(kept), 2)
        self.assertEqual(groups, [])

    def test_confirmed_tier_wins_deduplication_over_high_confidence_fallback(self) -> None:
        common = {"source": "same.mp4", "source_hash": "abc", "source_fps": 60,
                  "start": 0.0, "end": 4.0, "first_shot_time": 1.0, "event_time": 1.2,
                  "evidence": {"peak_phash": "0" * 64}}
        fallback = {**common, "confidence": .99, "label": "impact_candidate", "tier": "C", "weapon": None}
        confirmed = {**common, "confidence": .60, "label": "raider_knock_flare", "tier": "A", "weapon": "EQUALIZER"}
        fallback["id"], confirmed["id"] = arc.stable_event_id(fallback), arc.stable_event_id(confirmed)
        kept, groups = arc.deduplicate([fallback, confirmed])
        self.assertEqual(kept[0]["tier"], "A")
        self.assertEqual(groups[0]["duplicate_of"], confirmed["id"])


if __name__ == "__main__":
    unittest.main()
