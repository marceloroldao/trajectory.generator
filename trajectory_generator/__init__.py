"""trajectory.generator experimental API."""

from .core import (
    DEFAULT_CONFIG,
    MachineConfig,
    bits_to_bytes,
    bits_to_int,
    bytes_to_bits,
    encode_bits,
    int_to_bits,
    step_forward,
    step_inverse,
)
from .decode import DecodeResult, decode_exhaustive, decode_mitm, decode_mitm_partitioned, recover_unique
from .trajectory_address import DEFAULT_ADDRESS_CONFIG, TrajectoryAddressConfig, decode_trajectory_address, encode_trajectory_address
from .hierarchical_trajectory import DEFAULT_HIERARCHICAL_CONFIG, HierarchicalTrajectoryConfig, admissible_count, capacity_ok, decode_hierarchical_trajectory, encode_hierarchical_trajectory, rank_trajectory, unrank_trajectory
from .multiscale_trajectory import DEFAULT_MULTISCALE_CONFIG, MultiScaleTrajectoryConfig, address_envelope_count, capacity_ok as multiscale_capacity_ok, choose_mode, decode_multiscale_trajectory, deviation_count, encode_multiscale_trajectory, inverse_transform, per_mode_count, transform
from .recursive_trajectory import DEFAULT_RECURSIVE_CONFIG, RecursiveTrajectoryConfig, address_envelope_count as recursive_address_envelope_count, capacity_ok as recursive_capacity_ok, choose_level, decode_recursive_trajectory, deviation_count as recursive_deviation_count, encode_recursive_trajectory, inverse_level, inverse_relation_transform, per_level_count, relation_transform, transform_level
from .dyadic_trajectory_tree import DEFAULT_DYADIC_CONFIG, DyadicTrajectoryConfig, address_envelope_count as dyadic_address_envelope_count, capacity_ok as dyadic_capacity_ok, decode_dyadic_trajectory, encode_dyadic_trajectory
from .self_resolving_tree import DEFAULT_SELF_RESOLVING_CONFIG, SelfResolvingTreeConfig, address_envelope_count as self_resolving_address_envelope_count, capacity_ok as self_resolving_capacity_ok, decode_self_resolving_tree, encode_self_resolving_tree, leaf_radix as self_resolving_leaf_radix
from .admissible_trajectory import DEFAULT_ADMISSIBILITY_CONFIG, PeriodicAdmissibilityConfig, admissible_count as periodic_admissible_count, capacity_ok as periodic_capacity_ok, decode_admissible_trajectory, encode_admissible_trajectory, forced_bit, free_count, free_positions, is_forced_position, rank_admissible, unrank_admissible, validate_trajectory
from .state_admissibility import DEFAULT_STATE_ADMISSIBILITY_CONFIG, StateAdmissibilityConfig, admissible_count as state_admissible_count, allowed_next, capacity_ok as state_capacity_ok, decode_state_admissible, encode_state_admissible, rank_trajectory as rank_state_trajectory, unrank_trajectory as unrank_state_trajectory, validate_trajectory as validate_state_trajectory
from .finite_law_codec import (
    FORCE_0,
    FORCE_1,
    FREE,
    FiniteLawConfig,
    MEMORY3_PHI_RULE,
    MEMORY3_PLASTIC_RULE,
    MEMORY3_TRIBONACCI_RULE,
    admissible_count as finite_law_admissible_count,
    capacity_ok as finite_law_capacity_ok,
    decode_finite_law,
    encode_finite_law,
    rank_trajectory as rank_finite_law_trajectory,
    unrank_trajectory as unrank_finite_law_trajectory,
    validate as validate_finite_law_trajectory,
)
from .dynamic_law_codec import (
    DEFAULT_DYNAMIC_CONFIG,
    DynamicLawConfig,
    active_action as dynamic_active_action,
    active_rule_index as dynamic_active_rule_index,
    admissible_count as dynamic_admissible_count,
    capacity_ok as dynamic_capacity_ok,
    decode_dynamic_law,
    encode_dynamic_law,
    rank_trajectory as rank_dynamic_trajectory,
    unrank_trajectory as unrank_dynamic_trajectory,
    validate as validate_dynamic_trajectory,
)
from .coherence_universe import (
    DEFAULT_COHERENCE_UNIVERSE_CONFIG,
    CoherenceUniverseConfig,
    admissible_count as coherence_admissible_count,
    capacity_ok as coherence_capacity_ok,
    decode_coherence_universe,
    encode_coherence_universe,
    rank_trajectory as rank_coherence_trajectory,
    select_law as coherence_select_law,
    unrank_trajectory as unrank_coherence_trajectory,
    validate as validate_coherence_trajectory,
)
from .emergent_law_bank import (
    ALL_RULES as EMERGENT_MEMORY3_RULE_BANK,
    DEFAULT_EMERGENT_LAW_BANK_CONFIG,
    EmergentLawBankConfig,
    active_action as emergent_active_action,
    admissible_count as emergent_admissible_count,
    capacity_ok as emergent_capacity_ok,
    decode_emergent_law_bank,
    encode_emergent_law_bank,
    rank_trajectory as rank_emergent_trajectory,
    selected_rule_index as emergent_selected_rule_index,
    unrank_trajectory as unrank_emergent_trajectory,
    validate as validate_emergent_trajectory,
)

__all__ = [name for name in globals() if not name.startswith("_")]
