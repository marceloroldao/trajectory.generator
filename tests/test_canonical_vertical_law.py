import unittest

from trajectory_generator.canonical_vertical_law import (
    CANONICAL_PHASE_MERGE_SPEC,
    CanonicalPeriodicVerticalLift,
    CanonicalVerticalLawSpec,
    canonical_law_specs,
    derive_minimal_partition_law,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)


def phase_graph():
    return {
        ("a", 0): [("a", 1), ("b", 1)],
        ("b", 0): [("a", 1)],
        ("a", 1): [("a", 2)],
        ("b", 1): [("a", 2), ("b", 2)],
        ("a", 2): [("a", 0), ("b", 0)],
        ("b", 2): [("a", 0)],
    }


class CanonicalVerticalLawTests(unittest.TestCase):
    def build_machine(self):
        return build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )

    def test_grammar_has_no_free_numeric_coefficients(self):
        specs = canonical_law_specs()
        self.assertTrue(specs)
        self.assertEqual(
            specs[0].period_multiple,
            1,
        )
        for spec in specs:
            spec.validate()
            self.assertGreaterEqual(spec.term_count, 2)

    def test_structural_derivation_matches_frozen_law(self):
        self.assertEqual(
            derive_minimal_partition_law(),
            CANONICAL_PHASE_MERGE_SPEC,
        )
        self.assertEqual(
            CANONICAL_PHASE_MERGE_SPEC.period_multiple,
            1,
        )
        self.assertEqual(
            CANONICAL_PHASE_MERGE_SPEC.orientation_features,
            ("phase",),
        )
        self.assertEqual(
            CANONICAL_PHASE_MERGE_SPEC.shift_features,
            ("incoming_index",),
        )

    def test_simple_phase_merge_law_is_reversible(self):
        spec = CanonicalVerticalLawSpec(
            period_multiple=1,
            orientation_features=("phase",),
            shift_features=("incoming_index",),
        )
        lift = CanonicalPeriodicVerticalLift(
            self.build_machine(),
            spec,
        )

        nontrivial = 0
        flips = 0

        for time in range(12):
            for packed in range(lift.total_states(time)):
                state = lift.from_packed(
                    packed,
                    time,
                )
                for edge in lift.machine.codec.outgoing[
                    state.node
                ]:
                    drive = lift.drive(edge, time)
                    if drive.orientation == -1:
                        flips += 1

                    size = lift.fiber_size(
                        state.node,
                        time,
                    )
                    mapped = lift.permute_local(
                        state.vertical,
                        size,
                        drive,
                    )
                    if mapped != state.vertical:
                        nontrivial += 1

                    nxt = lift.advance(
                        state,
                        time,
                        edge.label,
                    )
                    previous, recovered = lift.rewind(
                        nxt,
                        time + 1,
                    )
                    self.assertEqual(previous, state)
                    self.assertEqual(recovered, edge)
                    self.assertEqual(
                        lift.project(nxt),
                        edge.target,
                    )

        self.assertGreater(nontrivial, 0)
        self.assertGreater(flips, 0)

    def test_drive_period_matches_selected_public_period(self):
        machine = self.build_machine()
        for multiple in (1, 2, 4):
            spec = CanonicalVerticalLawSpec(
                period_multiple=multiple,
                orientation_features=(
                    ("phase",)
                    if multiple == 1
                    else ("phase", "cycle")
                ),
                shift_features=("incoming_index",),
            )
            lift = CanonicalPeriodicVerticalLift(
                machine,
                spec,
            )
            for edge in lift.machine.codec.edges:
                for time in range(12):
                    self.assertEqual(
                        lift.drive(edge, time),
                        lift.drive(
                            edge,
                            time + lift.vertical_period,
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
