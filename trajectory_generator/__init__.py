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
from .decode import (
    DecodeResult,
    decode_exhaustive,
    decode_mitm,
    decode_mitm_partitioned,
    recover_unique,
)
from .trajectory_address import (
    DEFAULT_ADDRESS_CONFIG,
    TrajectoryAddressConfig,
    decode_trajectory_address,
    encode_trajectory_address,
)
from .hierarchical_trajectory import (
    DEFAULT_HIERARCHICAL_CONFIG,
    HierarchicalTrajectoryConfig,
    admissible_count,
    capacity_ok,
    decode_hierarchical_trajectory,
    encode_hierarchical_trajectory,
    rank_trajectory,
    unrank_trajectory,
)

__all__ = [
    "DEFAULT_CONFIG",
    "DEFAULT_ADDRESS_CONFIG",
    "DEFAULT_HIERARCHICAL_CONFIG",
    "MachineConfig",
    "TrajectoryAddressConfig",
    "HierarchicalTrajectoryConfig",
    "DecodeResult",
    "admissible_count",
    "bits_to_bytes",
    "bits_to_int",
    "bytes_to_bits",
    "capacity_ok",
    "decode_exhaustive",
    "decode_hierarchical_trajectory",
    "decode_mitm",
    "decode_mitm_partitioned",
    "decode_trajectory_address",
    "encode_bits",
    "encode_hierarchical_trajectory",
    "encode_trajectory_address",
    "int_to_bits",
    "rank_trajectory",
    "recover_unique",
    "step_forward",
    "step_inverse",
    "unrank_trajectory",
]
