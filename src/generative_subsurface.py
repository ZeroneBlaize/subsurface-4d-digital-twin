"""
Generative Subsurface Modeling Engine for the Indian Landmass.

Combines:
1. Indian Geological Provinces & Stratigraphic Knowledge Base (Indo-Gangetic, Deccan Basalt, Peninsular Archaean, Coastal Deltaic, Himalayan Foreland).
2. Coupled Markov Chain (CMC) & Transition Probability Model (Elfeki & Dekking formulation) for 1D, 2D, and 3D lithological sequence and cross-section synthesis.
3. Spatially Correlated Gaussian Random Fields for realistic stratum thickness continuity, pinch-out lenses, and geomorphic DEM generation.
4. Depth-dependent, IS:2131/IS:6403 calibrated SPT N-value, groundwater, and geotechnical parameter synthesis.
5. Automated calibration from real Indian borehole datasets (e.g. Shalimar Howrah, Deccan Basalt Benchmark).
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import math
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin, Affine
from rasterio.crs import CRS
from scipy.ndimage import gaussian_filter


# ---------------------------------------------------------------------------
# 1. INDIAN GEOLOGICAL PROVINCES REGISTRY & STRATUM DEFINITIONS
# ---------------------------------------------------------------------------

class IndianGeologicalProvince(str, Enum):
    INDO_GANGETIC_ALLUVIUM = "Indo-Gangetic Deep Alluvium"
    DECCAN_BASALT_TRAPS = "Deccan Basalt Traps"
    PENINSULAR_ARCHAEAN = "Peninsular Archaean / Granite Shield"
    COASTAL_DELTAIC = "Coastal Deltaic / Soft Marine Deposits"
    HIMALAYAN_FORELAND = "Himalayan Foreland / Shiwalik Belt"


@dataclass
class StratumProfile:
    """Geotechnical and lithological specification for a single stratum layer."""
    name: str
    soil_type: str
    thickness_mean: float
    thickness_std: float
    min_thickness: float = 0.4
    pinchout_prob: float = 0.0
    field_n_mean: float = 10.0
    field_n_std: float = 2.0
    n_depth_gradient: float = 0.5
    cohesion_kpa: float = 25.0
    friction_angle_deg: float = 15.0
    unit_weight_kn_m3: float = 18.0
    is_refusal: bool = False
    is_cohesive: bool = True


@dataclass
class ProvinceMetadata:
    """Regional metadata, typical cities, bounding coordinates, and default strata."""
    province: IndianGeologicalProvince
    description: str
    lat_range: Tuple[float, float]
    lon_range: Tuple[float, float]
    elevation_range: Tuple[float, float]
    water_table_depth_mean: float
    water_table_depth_std: float
    water_table_depth_min: float
    water_table_depth_max: float
    typical_cities: List[Tuple[str, float, float]]  # (City name, lat, lon)
    strata: List[StratumProfile]
    horizontal_k_values: List[float]  # Markov horizontal persistence factors (K = Lh / Lv)


PROVINCE_REGISTRY: Dict[IndianGeologicalProvince, ProvinceMetadata] = {
    IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM: ProvinceMetadata(
        province=IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM,
        description="Deep Quaternary alluvial plain deposited by the Indus-Ganga-Brahmaputra river systems. Thick sequences of silt, clay, and sand without shallow bedrock refusal.",
        lat_range=(24.5, 31.0),
        lon_range=(74.0, 88.0),
        elevation_range=(120.0, 240.0),
        water_table_depth_mean=3.8,
        water_table_depth_std=1.2,
        water_table_depth_min=1.5,
        water_table_depth_max=8.0,
        typical_cities=[
            ("Delhi", 28.6139, 77.2090),
            ("Kanpur", 26.4499, 80.3319),
            ("Lucknow", 26.8467, 80.9462),
            ("Patna", 25.5941, 85.1376),
            ("Varanasi", 25.3176, 82.9739),
            ("Chandigarh", 30.7333, 76.7794),
        ],
        strata=[
            StratumProfile(
                name="Topsoil / Alluvial Silt",
                soil_type="Clayey Silt (ML-CL)",
                thickness_mean=1.6,
                thickness_std=0.4,
                pinchout_prob=0.0,
                field_n_mean=6.0,
                field_n_std=1.5,
                n_depth_gradient=0.4,
                cohesion_kpa=14.0,
                friction_angle_deg=10.0,
                unit_weight_kn_m3=17.2,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Medium Stiff Silty Clay",
                soil_type="Inorganic Clay (CI)",
                thickness_mean=4.2,
                thickness_std=1.0,
                pinchout_prob=0.0,
                field_n_mean=10.0,
                field_n_std=2.5,
                n_depth_gradient=0.6,
                cohesion_kpa=36.0,
                friction_angle_deg=12.0,
                unit_weight_kn_m3=18.0,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Fine to Medium Sand",
                soil_type="Poorly Graded Sand (SP-SM)",
                thickness_mean=5.5,
                thickness_std=1.4,
                pinchout_prob=0.10,  # Sand lens pinch-out
                field_n_mean=22.0,
                field_n_std=4.0,
                n_depth_gradient=0.8,
                cohesion_kpa=4.0,
                friction_angle_deg=32.0,
                unit_weight_kn_m3=18.8,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Stiff Deep Alluvial Clay",
                soil_type="Stiff Clay (CH)",
                thickness_mean=8.5,
                thickness_std=2.0,
                pinchout_prob=0.0,
                field_n_mean=24.0,
                field_n_std=3.5,
                n_depth_gradient=0.5,
                cohesion_kpa=70.0,
                friction_angle_deg=14.0,
                unit_weight_kn_m3=19.4,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Dense Sand with Gravel",
                soil_type="Dense Sand / Gravel (SW-SM)",
                thickness_mean=6.0,
                thickness_std=1.5,
                pinchout_prob=0.0,
                field_n_mean=44.0,
                field_n_std=5.0,
                n_depth_gradient=1.0,
                cohesion_kpa=2.0,
                friction_angle_deg=36.0,
                unit_weight_kn_m3=20.5,
                is_refusal=True,
                is_cohesive=False,
            ),
        ],
        horizontal_k_values=[15.0, 20.0, 25.0, 18.0, 30.0],
    ),
    IndianGeologicalProvince.DECCAN_BASALT_TRAPS: ProvinceMetadata(
        province=IndianGeologicalProvince.DECCAN_BASALT_TRAPS,
        description="Upper Cretaceous to Eocene flood basalt continental volcanic province. Features black cotton soil, weathered murrum, vesicular weathered basalt, and massive columnar hard basalt bedrock.",
        lat_range=(16.0, 23.5),
        lon_range=(72.5, 80.5),
        elevation_range=(270.0, 650.0),
        water_table_depth_mean=4.1,
        water_table_depth_std=0.9,
        water_table_depth_min=2.0,
        water_table_depth_max=7.0,
        typical_cities=[
            ("Mumbai", 19.0760, 72.8777),
            ("Pune", 18.5204, 73.8567),
            ("Nagpur", 21.1458, 79.0882),
            ("Indore", 22.7196, 75.8577),
            ("Aurangabad", 19.8762, 75.3433),
            ("Nashik", 19.9975, 73.7898),
        ],
        strata=[
            StratumProfile(
                name="Topsoil / Fill",
                soil_type="Clayey Silt",
                thickness_mean=1.23,
                thickness_std=0.35,
                pinchout_prob=0.0,
                field_n_mean=5.8,
                field_n_std=1.5,
                n_depth_gradient=0.5,
                cohesion_kpa=15.0,
                friction_angle_deg=10.0,
                unit_weight_kn_m3=17.5,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Soft to Medium Silty Clay",
                soil_type="Inorganic Clay (CI)",
                thickness_mean=3.36,
                thickness_std=0.85,
                pinchout_prob=0.0,
                field_n_mean=10.1,
                field_n_std=2.6,
                n_depth_gradient=0.7,
                cohesion_kpa=35.0,
                friction_angle_deg=12.0,
                unit_weight_kn_m3=18.0,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Stiff Sandy Silt / Murrum",
                soil_type="Sandy Silt (ML)",
                thickness_mean=3.35,
                thickness_std=1.2,
                pinchout_prob=0.10,  # Prone to stratigraphic pinch-out in basalt flows
                field_n_mean=21.1,
                field_n_std=4.8,
                n_depth_gradient=1.1,
                cohesion_kpa=10.0,
                friction_angle_deg=28.0,
                unit_weight_kn_m3=19.0,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Weathered Basalt",
                soil_type="Weathered Rock",
                thickness_mean=4.06,
                thickness_std=0.9,
                pinchout_prob=0.0,
                field_n_mean=42.5,
                field_n_std=4.5,
                n_depth_gradient=1.4,
                cohesion_kpa=50.0,
                friction_angle_deg=34.0,
                unit_weight_kn_m3=21.0,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Hard Basalt (Bedrock)",
                soil_type="Hard Rock (Basalt)",
                thickness_mean=2.74,
                thickness_std=0.6,
                pinchout_prob=0.0,
                field_n_mean=80.7,
                field_n_std=12.0,
                n_depth_gradient=2.0,
                cohesion_kpa=150.0,
                friction_angle_deg=42.0,
                unit_weight_kn_m3=24.0,
                is_refusal=True,
                is_cohesive=False,
            ),
        ],
        horizontal_k_values=[12.0, 14.0, 10.0, 8.0, 20.0],
    ),
    IndianGeologicalProvince.PENINSULAR_ARCHAEAN: ProvinceMetadata(
        province=IndianGeologicalProvince.PENINSULAR_ARCHAEAN,
        description="Ancient Precambrian crystalline shield comprising charnockites, gneisses, and intrusive granites. Deep weathering profiles producing red sandy loam, saprolite, and irregular bedrock pinnacles.",
        lat_range=(8.0, 18.0),
        lon_range=(74.5, 81.0),
        elevation_range=(450.0, 950.0),
        water_table_depth_mean=6.5,
        water_table_depth_std=2.0,
        water_table_depth_min=3.0,
        water_table_depth_max=14.0,
        typical_cities=[
            ("Bengaluru", 12.9716, 77.5946),
            ("Hyderabad", 17.3850, 78.4867),
            ("Chennai (Inland / Tambaram)", 12.9249, 80.1000),
            ("Mysuru", 12.2958, 76.6394),
            ("Coimbatore", 11.0168, 76.9558),
            ("Ranchi", 23.3441, 85.3096),
        ],
        strata=[
            StratumProfile(
                name="Red Gravelly Topsoil / Fill",
                soil_type="Silty Sand with Gravel (SM)",
                thickness_mean=1.1,
                thickness_std=0.3,
                pinchout_prob=0.0,
                field_n_mean=7.0,
                field_n_std=2.0,
                n_depth_gradient=0.5,
                cohesion_kpa=12.0,
                friction_angle_deg=16.0,
                unit_weight_kn_m3=17.6,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Medium Stiff Red Sandy Clay",
                soil_type="Inorganic Clay with Sand (CL)",
                thickness_mean=3.2,
                thickness_std=0.8,
                pinchout_prob=0.0,
                field_n_mean=14.0,
                field_n_std=3.0,
                n_depth_gradient=0.8,
                cohesion_kpa=42.0,
                friction_angle_deg=18.0,
                unit_weight_kn_m3=18.4,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Weathered Granite / Saprolite",
                soil_type="Silty Sand / Decomposed Granite (SM)",
                thickness_mean=4.8,
                thickness_std=1.5,
                pinchout_prob=0.05,
                field_n_mean=32.0,
                field_n_std=6.0,
                n_depth_gradient=1.2,
                cohesion_kpa=22.0,
                friction_angle_deg=33.0,
                unit_weight_kn_m3=19.8,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Moderately Weathered Fractured Granite",
                soil_type="Weathered Rock (Granite)",
                thickness_mean=4.0,
                thickness_std=1.2,
                pinchout_prob=0.05,
                field_n_mean=58.0,
                field_n_std=8.0,
                n_depth_gradient=1.8,
                cohesion_kpa=75.0,
                friction_angle_deg=38.0,
                unit_weight_kn_m3=22.5,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Hard Crystalline Granite Bedrock",
                soil_type="Hard Rock (Charnockite / Granite)",
                thickness_mean=3.0,
                thickness_std=0.8,
                pinchout_prob=0.0,
                field_n_mean=88.0,
                field_n_std=10.0,
                n_depth_gradient=2.5,
                cohesion_kpa=200.0,
                friction_angle_deg=44.0,
                unit_weight_kn_m3=25.5,
                is_refusal=True,
                is_cohesive=False,
            ),
        ],
        horizontal_k_values=[10.0, 12.0, 8.0, 7.0, 15.0],
    ),
    IndianGeologicalProvince.COASTAL_DELTAIC: ProvinceMetadata(
        province=IndianGeologicalProvince.COASTAL_DELTAIC,
        description="Holocene-Pleistocene deltaic, estuarine, and marine tidal deposits. Characterized by soft organic peaty clays, high groundwater table (<1.5m), high compressibility, and dense basal sands.",
        lat_range=(20.5, 23.8),
        lon_range=(86.5, 89.5),
        elevation_range=(2.0, 25.0),
        water_table_depth_mean=1.02,
        water_table_depth_std=0.43,
        water_table_depth_min=0.3,
        water_table_depth_max=2.0,
        typical_cities=[
            ("Howrah (Shalimar)", 22.5600, 88.3100),
            ("Kolkata", 22.5726, 88.3639),
            ("Haldia", 22.0644, 88.0698),
            ("Kakinada", 16.9891, 82.2475),
            ("Kochi", 9.9312, 76.2673),
            ("Surat (Coastal)", 21.1702, 72.8311),
        ],
        strata=[
            StratumProfile(
                name="Topsoil / Fill",
                soil_type="Fill / Clayey Silt",
                thickness_mean=2.16,
                thickness_std=0.45,
                pinchout_prob=0.0,
                field_n_mean=4.9,
                field_n_std=0.8,
                n_depth_gradient=0.3,
                cohesion_kpa=12.0,
                friction_angle_deg=8.0,
                unit_weight_kn_m3=17.0,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Firm Brown Silty Clay",
                soil_type="Inorganic Clay (CH-MH)",
                thickness_mean=4.13,
                thickness_std=0.7,
                pinchout_prob=0.0,
                field_n_mean=7.3,
                field_n_std=1.2,
                n_depth_gradient=0.5,
                cohesion_kpa=38.0,
                friction_angle_deg=12.0,
                unit_weight_kn_m3=18.2,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Soft Peaty Silty Clay",
                soil_type="Organic Peaty Clay (CH-OH)",
                thickness_mean=7.15,
                thickness_std=1.3,
                pinchout_prob=0.0,
                field_n_mean=2.8,
                field_n_std=0.8,
                n_depth_gradient=0.2,
                cohesion_kpa=18.0,
                friction_angle_deg=4.0,
                unit_weight_kn_m3=16.5,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Stiff Bluish Grey Clay",
                soil_type="Stiff Clay (CH-MH)",
                thickness_mean=13.15,
                thickness_std=1.8,
                pinchout_prob=0.0,
                field_n_mean=18.1,
                field_n_std=2.6,
                n_depth_gradient=0.7,
                cohesion_kpa=65.0,
                friction_angle_deg=16.0,
                unit_weight_kn_m3=19.5,
                is_refusal=False,
                is_cohesive=True,
            ),
            StratumProfile(
                name="Dense Silty Sand",
                soil_type="Silty Sand (SM-ML)",
                thickness_mean=6.80,
                thickness_std=1.2,
                pinchout_prob=0.0,
                field_n_mean=40.8,
                field_n_std=5.0,
                n_depth_gradient=1.2,
                cohesion_kpa=5.0,
                friction_angle_deg=34.0,
                unit_weight_kn_m3=20.5,
                is_refusal=True,
                is_cohesive=False,
            ),
        ],
        horizontal_k_values=[18.0, 22.0, 25.0, 20.0, 30.0],
    ),
    IndianGeologicalProvince.HIMALAYAN_FORELAND: ProvinceMetadata(
        province=IndianGeologicalProvince.HIMALAYAN_FORELAND,
        description="Sub-Himalayan foreland and Shiwalik belt comprising coarse boulder-gravel beds, molasse sediments, fluvial terraces, and interbedded sandstones.",
        lat_range=(27.0, 33.5),
        lon_range=(74.0, 94.0),
        elevation_range=(350.0, 1100.0),
        water_table_depth_mean=8.2,
        water_table_depth_std=3.0,
        water_table_depth_min=4.0,
        water_table_depth_max=20.0,
        typical_cities=[
            ("Dehradun", 30.3165, 78.0322),
            ("Jammu", 32.7266, 74.8570),
            ("Siliguri", 26.7271, 88.3953),
            ("Guwahati", 26.1445, 91.7362),
            ("Rishikesh", 30.0869, 78.2676),
        ],
        strata=[
            StratumProfile(
                name="Coarse Topsoil with Cobbles",
                soil_type="Gravelly Silt / Colluvium (GM)",
                thickness_mean=1.2,
                thickness_std=0.4,
                pinchout_prob=0.0,
                field_n_mean=9.0,
                field_n_std=2.5,
                n_depth_gradient=0.8,
                cohesion_kpa=10.0,
                friction_angle_deg=26.0,
                unit_weight_kn_m3=18.0,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Coarse Sandy Silt / Gravel",
                soil_type="Silty Gravel with Sand (GM-GP)",
                thickness_mean=3.5,
                thickness_std=1.0,
                pinchout_prob=0.0,
                field_n_mean=22.0,
                field_n_std=4.5,
                n_depth_gradient=1.2,
                cohesion_kpa=16.0,
                friction_angle_deg=32.0,
                unit_weight_kn_m3=19.5,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Dense Fluvial Cobble-Gravel Bed",
                soil_type="Cobble Gravel Bed (GP)",
                thickness_mean=5.2,
                thickness_std=1.4,
                pinchout_prob=0.08,
                field_n_mean=48.0,
                field_n_std=7.0,
                n_depth_gradient=1.6,
                cohesion_kpa=8.0,
                friction_angle_deg=38.0,
                unit_weight_kn_m3=21.5,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Weak Sandstone / Mudstone Interbed",
                soil_type="Soft Rock / Mudstone",
                thickness_mean=4.5,
                thickness_std=1.2,
                pinchout_prob=0.05,
                field_n_mean=65.0,
                field_n_std=9.0,
                n_depth_gradient=2.0,
                cohesion_kpa=70.0,
                friction_angle_deg=35.0,
                unit_weight_kn_m3=22.5,
                is_refusal=False,
                is_cohesive=False,
            ),
            StratumProfile(
                name="Competent Sedimentary Bedrock",
                soil_type="Hard Sandstone / Bedrock",
                thickness_mean=3.2,
                thickness_std=0.8,
                pinchout_prob=0.0,
                field_n_mean=90.0,
                field_n_std=10.0,
                n_depth_gradient=2.5,
                cohesion_kpa=130.0,
                friction_angle_deg=40.0,
                unit_weight_kn_m3=24.5,
                is_refusal=True,
                is_cohesive=False,
            ),
        ],
        horizontal_k_values=[10.0, 15.0, 20.0, 12.0, 18.0],
    ),
}


# ---------------------------------------------------------------------------
# 2. COUPLED MARKOV CHAIN (CMC) MODEL (Elfeki & Dekking formulation)
# ---------------------------------------------------------------------------

class CoupledMarkovModel:
    """
    Coupled Markov Chain model for vertical & horizontal lithological transitions.
    Based on the Elfeki & Dekking (2001, 2005) formulation.
    """

    def __init__(self, num_states: int, k_values: Optional[List[float]] = None):
        self.num_states = num_states
        self.k_values = np.array(k_values, dtype=np.float64) if k_values is not None else np.full(num_states, 12.0)
        self.vertical_prob: np.ndarray = np.eye(num_states, dtype=np.float64)
        self.horizontal_prob_1step: np.ndarray = np.eye(num_states, dtype=np.float64)

    @staticmethod
    def row_normalize(matrix: np.ndarray) -> np.ndarray:
        """Ensures every row of a transition frequency matrix sums to 1.0."""
        prob = np.zeros_like(matrix, dtype=np.float64)
        for r in range(matrix.shape[0]):
            r_sum = matrix[r].sum()
            if r_sum > 0:
                prob[r] = matrix[r] / r_sum
            else:
                prob[r, r] = 1.0
        return prob

    def fit_from_sequences(self, sequences: List[List[int]]):
        """
        Calculates vertical transition frequencies from a collection of 1D layer state sequences
        and computes horizontal transition probabilities scaled by persistence K.
        State indices must be 0-based integers in [0, num_states - 1].
        """
        vert_freq = np.zeros((self.num_states, self.num_states), dtype=np.float64)
        bottom_to_top = np.zeros((self.num_states, self.num_states), dtype=np.float64)

        for seq in sequences:
            for i in range(len(seq) - 1):
                from_s = seq[i]
                to_s = seq[i + 1]
                if 0 <= from_s < self.num_states and 0 <= to_s < self.num_states:
                    vert_freq[from_s, to_s] += 1.0
            for i in range(len(seq) - 1, 0, -1):
                from_s = seq[i]
                to_s = seq[i - 1]
                if 0 <= from_s < self.num_states and 0 <= to_s < self.num_states:
                    bottom_to_top[from_s, to_s] += 1.0

        # Regularize zero rows with diagonal persistence
        for s in range(self.num_states):
            if vert_freq[s].sum() == 0:
                vert_freq[s, s] = 10.0
                if s + 1 < self.num_states:
                    vert_freq[s, s + 1] = 5.0
            if bottom_to_top[s].sum() == 0:
                bottom_to_top[s, s] = 10.0

        self.vertical_prob = self.row_normalize(vert_freq)

        # Horizontal transition frequency derived with persistence scaling K
        horiz_freq = bottom_to_top.copy()
        for s in range(self.num_states):
            k_val = self.k_values[s] if s < len(self.k_values) else 10.0
            horiz_freq[s, s] = max(1.0, k_val * bottom_to_top[s, s])

        self.horizontal_prob_1step = self.row_normalize(horiz_freq)

    def get_horizontal_prob(self, distance: int) -> np.ndarray:
        """Calculates d-step horizontal transition probability via matrix power."""
        if distance <= 1:
            return self.horizontal_prob_1step
        return np.linalg.matrix_power(self.horizontal_prob_1step, distance)

    def simulate_1d_sequence(self, num_steps: int, initial_state: int = 0, rng: Optional[np.random.Generator] = None) -> List[int]:
        """Simulates a 1D vertical Markov chain sequence of strata."""
        if rng is None:
            rng = np.random.default_rng()
        seq = [initial_state]
        curr = initial_state
        for _ in range(num_steps - 1):
            probs = self.vertical_prob[curr]
            curr = int(rng.choice(self.num_states, p=probs))
            seq.append(curr)
        return seq

    @staticmethod
    def sample_discrete(weights: np.ndarray, rng: Optional[np.random.Generator] = None) -> int:
        """Samples a discrete state 0 <= s < num_states from non-negative weights."""
        if rng is None:
            rng = np.random.default_rng()
        w = np.asarray(weights, dtype=np.float64).ravel()
        w_sum = w.sum()
        if not np.isfinite(w_sum) or w_sum <= 0:
            probs = np.ones(len(w), dtype=np.float64) / len(w)
        else:
            probs = w / w_sum
        return int(rng.choice(len(probs), p=probs))

    @staticmethod
    def choose_direction(
        left: int, left_above: int,
        right: int, right_above: int,
        prev_direction: int,
        h_prob_spacing: np.ndarray,
        rng: np.random.Generator
    ) -> int:
        """
        Elfeki & Dekking (2001, 2005) directional selection rule.
        Returns 1 for Left-to-Right, 2 for Right-to-Left.
        """
        if left == right and left == left_above and right != right_above:
            return 1
        elif left == right and left != left_above and right == right_above:
            return 2
        elif left != left_above and right == right_above:
            return 1
        elif left == left_above and right != right_above:
            return 2
        elif left == left_above and right == right_above:
            return prev_direction
        else:
            p_lr = h_prob_spacing[left, right]
            p_rl = h_prob_spacing[right, left]
            tot = p_lr + p_rl
            p1 = (p_lr / tot) if tot > 0 else 0.5
            return 1 if rng.uniform() < p1 else 2

    def simulate_interval_left_to_right(
        self,
        prev_row: np.ndarray,
        left_val: int,
        right_val: int,
        interval_width: int,
        h_prob_powers: Dict[int, np.ndarray],
        rng: np.random.Generator
    ) -> np.ndarray:
        """Simulates one interval row from left to right."""
        row_vals = np.zeros(interval_width, dtype=np.int32)
        row_vals[0] = left_val
        row_vals[-1] = right_val

        for c in range(1, interval_width - 1):
            v_state = prev_row[c]
            l_state = row_vals[c - 1]
            r_target = right_val
            dist_to_r = interval_width - 1 - c

            weights = np.zeros(self.num_states, dtype=np.float64)
            h_power = h_prob_powers.get(dist_to_r, self.horizontal_prob_1step)
            for s in range(self.num_states):
                pv = self.vertical_prob[v_state, s]
                ph_l = self.horizontal_prob_1step[l_state, s]
                ph_r = h_power[s, r_target]
                weights[s] = pv * ph_l * ph_r

            row_vals[c] = self.sample_discrete(weights, rng)
        return row_vals

    def simulate_interval_right_to_left(
        self,
        prev_row: np.ndarray,
        left_val: int,
        right_val: int,
        interval_width: int,
        h_prob_powers: Dict[int, np.ndarray],
        rng: np.random.Generator
    ) -> np.ndarray:
        """Simulates one interval row from right to left."""
        row_vals = np.zeros(interval_width, dtype=np.int32)
        row_vals[0] = left_val
        row_vals[-1] = right_val

        for c in range(interval_width - 2, 0, -1):
            v_state = prev_row[c]
            r_state = row_vals[c + 1]
            l_target = left_val
            dist_to_l = c

            weights = np.zeros(self.num_states, dtype=np.float64)
            h_power = h_prob_powers.get(dist_to_l, self.horizontal_prob_1step)
            for s in range(self.num_states):
                pv = self.vertical_prob[v_state, s]
                ph_r = self.horizontal_prob_1step[r_state, s]
                ph_l = h_power[s, l_target]
                weights[s] = pv * ph_r * ph_l

            row_vals[c] = self.sample_discrete(weights, rng)
        return row_vals

    def simulate_2d_profile(
        self,
        conditioning_cols: List[int],
        conditioning_layers: np.ndarray,  # shape (num_rows, num_cond)
        num_cols: int,
        num_rows: int,
        rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """
        Simulates a 2D conditioned cross-section profile using Coupled Markov Chains.
        Enforces exact conditioning at specified borehole columns with bidirectional sampling.
        """
        if rng is None:
            rng = np.random.default_rng()

        num_cond = len(conditioning_cols)
        profile = np.zeros((num_rows, num_cols), dtype=np.int32)

        # Set top row from mode of conditioning collars
        top_mode = int(np.round(np.median(conditioning_layers[0, :])))
        profile[0, :] = np.clip(top_mode, 0, self.num_states - 1)

        # Stamp conditioning boreholes
        for i, c_col in enumerate(conditioning_cols):
            profile[:, c_col] = conditioning_layers[:, i]

        # Extrapolate left and right edges if needed
        if conditioning_cols[0] > 0:
            for c in range(conditioning_cols[0]):
                profile[:, c] = conditioning_layers[:, 0]
        if conditioning_cols[-1] < num_cols - 1:
            for c in range(conditioning_cols[-1] + 1, num_cols):
                profile[:, c] = conditioning_layers[:, -1]

        # Precompute horizontal transition matrices up to max interval spacing
        spacing = [conditioning_cols[i + 1] - conditioning_cols[i] for i in range(num_cond - 1)]
        max_dist = max(spacing) if spacing else 1
        h_prob_powers = {d: self.get_horizontal_prob(d) for d in range(1, max_dist + 1)}

        # Simulate intervals between consecutive conditioning boreholes
        for i in range(num_cond - 1):
            left_col = conditioning_cols[i]
            right_col = conditioning_cols[i + 1]
            dist_lr = right_col - left_col
            if dist_lr <= 1:
                continue

            interval_width = dist_lr + 1

            # Simulate top row (row 0) between left_col and right_col via 1D horizontal Markov bridge
            l_top = profile[0, left_col]
            r_top = profile[0, right_col]
            if l_top == r_top:
                profile[0, left_col:right_col + 1] = l_top
            else:
                top_row_vals = np.zeros(interval_width, dtype=np.int32)
                top_row_vals[0] = l_top
                top_row_vals[-1] = r_top
                for c in range(1, interval_width - 1):
                    prev_s = top_row_vals[c - 1]
                    dist_to_r = interval_width - 1 - c
                    h_power = h_prob_powers.get(dist_to_r, self.horizontal_prob_1step)
                    weights = self.horizontal_prob_1step[prev_s, :] * h_power[:, r_top]
                    top_row_vals[c] = self.sample_discrete(weights, rng)
                profile[0, left_col:right_col + 1] = top_row_vals

            # Initial direction at top row from 1-step horizontal transition
            p_lr_init = self.horizontal_prob_1step[profile[0, left_col], profile[0, right_col]]
            p_rl_init = self.horizontal_prob_1step[profile[0, right_col], profile[0, left_col]]
            direction = self.sample_discrete(np.array([p_lr_init, p_rl_init]), rng) + 1

            for row in range(1, num_rows):
                left_val = profile[row, left_col]
                left_above = profile[row - 1, left_col]
                right_val = profile[row, right_col]
                right_above = profile[row - 1, right_col]

                spacing_prob = h_prob_powers.get(dist_lr, self.horizontal_prob_1step)
                direction = self.choose_direction(
                    left_val, left_above,
                    right_val, right_above,
                    direction,
                    spacing_prob,
                    rng
                )

                prev_row_slice = profile[row - 1, left_col:right_col + 1]
                if direction == 1:
                    profile[row, left_col:right_col + 1] = self.simulate_interval_left_to_right(
                        prev_row_slice, left_val, right_val, interval_width, h_prob_powers, rng
                    )
                else:
                    profile[row, left_col:right_col + 1] = self.simulate_interval_right_to_left(
                        prev_row_slice, left_val, right_val, interval_width, h_prob_powers, rng
                    )

        return profile

    @staticmethod
    def compute_information_entropy(realizations: List[np.ndarray], num_states: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes cell-wise layer occurrence probabilities and Shannon information entropy:
        H(x, z) = - sum(p_i * log2(p_i)).
        Returns:
            (probabilities_3d, entropy_2d)
        """
        num_sims = len(realizations)
        num_rows, num_cols = realizations[0].shape
        prob_3d = np.zeros((num_states, num_rows, num_cols), dtype=np.float32)

        for r in realizations:
            for s in range(num_states):
                prob_3d[s] += (r == s).astype(np.float32)
        prob_3d /= max(1, num_sims)

        # Shannon Entropy
        entropy = np.zeros((num_rows, num_cols), dtype=np.float32)
        for s in range(num_states):
            p = prob_3d[s]
            nz = p > 1e-7
            entropy[nz] -= p[nz] * np.log2(p[nz])

        return prob_3d, entropy


# ---------------------------------------------------------------------------
# 3. SPATIAL RANDOM FIELD & DEM TOPOGRAPHY SYNTHESIZER
# ---------------------------------------------------------------------------

class SpatialFieldSynthesizer:
    """
    Generates spatially continuous 2D Gaussian random fields with controlled correlation lengths,
    used to create realistic topography (DEM) and smooth geological stratum thickness fields.
    """

    @staticmethod
    def generate_gaussian_field(
        nx: int,
        ny: int,
        correlation_length_cells: float = 25.0,
        rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """Generates a zero-mean, unit-variance 2D Gaussian random field via Gaussian filtering."""
        if rng is None:
            rng = np.random.default_rng()
        white_noise = rng.standard_normal((ny, nx))
        smoothed = gaussian_filter(white_noise, sigma=correlation_length_cells, mode="reflect")
        std = smoothed.std()
        if std > 1e-7:
            smoothed = (smoothed - smoothed.mean()) / std
        return smoothed.astype(np.float32)

    @staticmethod
    def synthesize_terrain_dem(
        province: IndianGeologicalProvince,
        nx: int = 150,
        ny: int = 150,
        resolution: float = 10.0,
        rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """
        Synthesizes realistic 2D Digital Elevation Model topography matching the geomorphic character
        of the specified Indian geological province.
        """
        if rng is None:
            rng = np.random.default_rng()

        meta = PROVINCE_REGISTRY[province]
        min_elev, max_elev = meta.elevation_range
        base_elev = (min_elev + max_elev) / 2.0
        elev_range = max_elev - min_elev

        x = np.linspace(0, (nx - 1) * resolution, nx)
        y = np.linspace(0, (ny - 1) * resolution, ny)
        X, Y = np.meshgrid(x, y)

        if province == IndianGeologicalProvince.COASTAL_DELTAIC:
            # Low, flat coastal river delta with micro-relief and gentle drainage gradient
            gradient = 0.0008 * (Y - X)
            micro = 1.2 * np.sin(2 * np.pi * X / 800.0) * np.cos(2 * np.pi * Y / 700.0)
            field = SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=40.0, rng=rng)
            raw = base_elev + gradient + micro + (field * 0.8)

        elif province == IndianGeologicalProvince.DECCAN_BASALT_TRAPS:
            # Undulating basalt flows, stepped terraces, and valley-ridge topography
            regional_slope = 0.003 * (Y - 0.5 * X)
            terrace = 6.0 * np.sin(2 * np.pi * X / 1200.0) * np.cos(2 * np.pi * Y / 1000.0)
            undulations = 3.5 * np.cos(2 * np.pi * (X + Y) / 600.0)
            field = SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=20.0, rng=rng)
            raw = base_elev + regional_slope + terrace + undulations + (field * 2.5)

        elif province == IndianGeologicalProvince.PENINSULAR_ARCHAEAN:
            # Pediplain with residual granite knolls (kopjes / inselbergs)
            kopjes = 14.0 * np.exp(-((X - nx * resolution * 0.6)**2 + (Y - ny * resolution * 0.4)**2) / (500.0**2))
            regional = 0.005 * (X + 0.3 * Y)
            field = SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=25.0, rng=rng)
            raw = base_elev + regional + kopjes + (field * 4.0)

        elif province == IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM:
            # Vast flat alluvial plain, gentle downstream slope with subtle paleochannels
            slope = 0.001 * (Y + X)
            paleochannel = -2.5 * np.exp(-((Y - 0.5 * X - 200.0)**2) / (300.0**2))
            field = SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=50.0, rng=rng)
            raw = base_elev + slope + paleochannel + (field * 1.5)

        elif province == IndianGeologicalProvince.HIMALAYAN_FORELAND:
            # Piedmont alluvial fan slope with incised seasonal torrents (choes/raos)
            slope = 0.02 * Y  # Steeper piedmont slope
            channels = 4.0 * np.sin(2 * np.pi * X / 400.0)
            field = SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=15.0, rng=rng)
            raw = base_elev + slope + channels + (field * 6.0)

        else:
            raw = base_elev + SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=20.0, rng=rng) * 5.0

        # Clamp strictly within realistic physical bounds
        clamped = np.clip(raw, min_elev, max_elev).astype(np.float32)
        return clamped


# ---------------------------------------------------------------------------
# 4. DATA CALIBRATION FROM REAL INDIAN BOREHOLE DATASETS
# ---------------------------------------------------------------------------

class GeotechnicalCalibrator:
    """
    Ingests real Indian geotechnical datasets (e.g. Shalimar Howrah, Deccan benchmark),
    fits empirical stratum parameters, transition frequencies, and SPT regressions.
    """

    @staticmethod
    def calibrate_from_dataframe(df: pd.DataFrame) -> Dict:
        """
        Extracts empirical layer parameters from an existing standardized borehole DataFrame.
        """
        # Standardize column naming
        cols = {c.strip(): c.strip() for c in df.columns}
        df_clean = df.copy()

        calibrated = {
            "strata_stats": {},
            "layer_names": [],
            "water_table_mean": 3.0,
            "water_table_std": 1.0,
            "transition_sequences": [],
        }

        if "Water_Table_Depth_m" in df_clean.columns:
            wt_series = df_clean["Water_Table_Depth_m"].dropna()
            if len(wt_series) > 0:
                calibrated["water_table_mean"] = float(wt_series.mean())
                calibrated["water_table_std"] = float(wt_series.std()) if len(wt_series) > 1 else 0.5

        if "Layer_Name" not in df_clean.columns:
            return calibrated

        # Group by Layer_Name
        for name, grp in df_clean.groupby("Layer_Name"):
            calibrated["layer_names"].append(name)
            t_mean = float(grp["Thickness_m"].mean()) if "Thickness_m" in grp.columns else 3.0
            t_std = float(grp["Thickness_m"].std()) if "Thickness_m" in grp.columns and len(grp) > 1 else 0.8
            n_mean = float(grp["Field_N"].mean()) if "Field_N" in grp.columns else 15.0
            n_std = float(grp["Field_N"].std()) if "Field_N" in grp.columns and len(grp) > 1 else 3.0
            c_mean = float(grp["Cohesion_kPa"].mean()) if "Cohesion_kPa" in grp.columns else 20.0
            phi_mean = float(grp["Friction_Angle_deg"].mean()) if "Friction_Angle_deg" in grp.columns else 15.0
            gamma_mean = float(grp["Unit_Weight_kN_m3"].mean()) if "Unit_Weight_kN_m3" in grp.columns else 18.0
            pinchout_rate = float((grp["Thickness_m"] == 0).mean()) if "Thickness_m" in grp.columns else 0.0

            calibrated["strata_stats"][name] = {
                "thickness_mean": t_mean,
                "thickness_std": max(0.2, t_std),
                "field_n_mean": max(1.0, n_mean),
                "field_n_std": max(1.0, n_std),
                "cohesion_kpa": c_mean,
                "friction_angle_deg": phi_mean,
                "unit_weight_kn_m3": gamma_mean,
                "pinchout_prob": pinchout_rate,
            }

        # Extract sequence of strata per borehole
        if "Borehole_ID" in df_clean.columns:
            for _, bh_grp in df_clean.groupby("Borehole_ID"):
                seq = bh_grp.sort_values(by="Depth_From_m" if "Depth_From_m" in bh_grp.columns else "Depth_To_m")["Layer_Name"].tolist()
                calibrated["transition_sequences"].append(seq)

        return calibrated

    @staticmethod
    def calibrate_from_cmc_boreholedata(cmc_dir: Union[str, Path]) -> Dict:
        """
        Parses and calibrates from CoupledMarkov example benchmark dataset:
        case_config.csv, soil_types.csv, boreholes.csv, and borehole_layers.csv.
        """
        cmc_path = Path(cmc_dir)
        config_path = cmc_path / "case_config.csv"
        soils_path = cmc_path / "soil_types.csv"
        bhs_path = cmc_path / "boreholes.csv"
        layers_path = cmc_path / "borehole_layers.csv"

        calibrated = {
            "config": {},
            "soil_types": {},
            "boreholes": [],
            "k_values": [],
            "discretized_sequences": [],
            "strata_stats": {},
            "layer_names": [],
        }

        # 1. Config
        if config_path.exists():
            cfg_df = pd.read_csv(config_path)
            for _, r in cfg_df.iterrows():
                calibrated["config"][str(r["parameter"]).strip()] = str(r["value"]).strip()
            if "k_values" in calibrated["config"]:
                calibrated["k_values"] = [float(k) for k in calibrated["config"]["k_values"].split()]

        # 2. Soil types
        if soils_path.exists():
            soils_df = pd.read_csv(soils_path)
            for _, r in soils_df.iterrows():
                lid = int(r["layer_id"])
                sname = str(r["soil_name"]).strip()
                calibrated["soil_types"][lid] = sname
                calibrated["layer_names"].append(sname)

        # 3. Boreholes
        if bhs_path.exists():
            bhs_df = pd.read_csv(bhs_path)
            calibrated["boreholes"] = bhs_df.to_dict(orient="records")

        # 4. Discretized layers
        if layers_path.exists():
            layers_df = pd.read_csv(layers_path)
            for _, grp in layers_df.groupby("borehole_id"):
                seq = grp.sort_values(by="depth_m")["layer_id"].tolist()
                seq_0based = [int(sid) - 1 for sid in seq if int(sid) >= 1]
                if len(seq_0based) > 0:
                    calibrated["discretized_sequences"].append(seq_0based)

            dz = float(calibrated["config"].get("dz_m", 0.5))
            for lid, sname in calibrated["soil_types"].items():
                counts = []
                for seq in calibrated["discretized_sequences"]:
                    c = sum(1 for s in seq if s == (lid - 1))
                    counts.append(c * dz)
                counts_arr = np.array(counts)
                calibrated["strata_stats"][sname] = {
                    "thickness_mean": float(counts_arr.mean()) if len(counts_arr) > 0 else 3.0,
                    "thickness_std": float(counts_arr.std()) if len(counts_arr) > 1 else 1.0,
                }

        return calibrated


# ---------------------------------------------------------------------------
# 5. HIGH-LEVEL INDIAN SUBSURFACE GENERATIVE ENGINE
# ---------------------------------------------------------------------------

class IndianSubsurfaceSynthesizer:
    """
    Main generative subsurface modeling engine for the Indian landmass.
    Synthesizes georeferenced DEM rasters, realistic 3D borehole logs,
    and Coupled Markov 2D/3D stratigraphy profiles conditioned on geographic location.
    """

    def __init__(self, calibrate_on_defaults: bool = True):
        import copy
        self.province_metadata = copy.deepcopy(PROVINCE_REGISTRY)
        self.calibrated_data: Dict[IndianGeologicalProvince, Dict] = {}
        self.calibrated_cmc_data: Optional[Dict] = None
        if calibrate_on_defaults:
            self._calibrate_builtin_datasets()

    def _calibrate_builtin_datasets(self):
        """Loads and calibrates against the Howrah real dataset, Deccan benchmark, and CoupledMarkov benchmark."""
        from src.config import PROJECT_ROOT
        howrah_csv = PROJECT_ROOT / "data/raw/howrah_boreholes_parsed.csv"
        deccan_csv = PROJECT_ROOT / "data/benchmark/boreholes_benchmark.csv"
        cmc_dir = PROJECT_ROOT / "data/raw/CoupledMarkov/examples/boreholedata"

        if howrah_csv.exists():
            df_h = pd.read_csv(howrah_csv)
            self.calibrated_data[IndianGeologicalProvince.COASTAL_DELTAIC] = GeotechnicalCalibrator.calibrate_from_dataframe(df_h)
            self._apply_calibrated_parameters(IndianGeologicalProvince.COASTAL_DELTAIC)

        if deccan_csv.exists():
            df_d = pd.read_csv(deccan_csv)
            self.calibrated_data[IndianGeologicalProvince.DECCAN_BASALT_TRAPS] = GeotechnicalCalibrator.calibrate_from_dataframe(df_d)
            self._apply_calibrated_parameters(IndianGeologicalProvince.DECCAN_BASALT_TRAPS)

        if cmc_dir.exists():
            self.calibrated_cmc_data = GeotechnicalCalibrator.calibrate_from_cmc_boreholedata(cmc_dir)

    def _apply_calibrated_parameters(self, province: IndianGeologicalProvince):
        """Applies empirical calibrated stratum and groundwater statistics to active province metadata."""
        if province not in self.calibrated_data:
            return
        calib = self.calibrated_data[province]
        meta = self.province_metadata[province]

        if "water_table_mean" in calib:
            meta.water_table_depth_mean = calib["water_table_mean"]
            meta.water_table_depth_std = calib.get("water_table_std", meta.water_table_depth_std)

        strata_stats = calib.get("strata_stats", {})
        for stratum in meta.strata:
            matched_key = None
            s_name = stratum.name.lower().strip()
            for k in strata_stats:
                k_clean = k.lower().strip()
                if k_clean == s_name or k_clean in s_name or s_name in k_clean:
                    matched_key = k
                    break
            if matched_key is not None:
                st = strata_stats[matched_key]
                stratum.thickness_mean = st["thickness_mean"]
                stratum.thickness_std = st["thickness_std"]
                stratum.field_n_mean = st["field_n_mean"]
                stratum.field_n_std = st["field_n_std"]
                stratum.pinchout_prob = st["pinchout_prob"]
                stratum.cohesion_kpa = st["cohesion_kpa"]
                stratum.friction_angle_deg = st["friction_angle_deg"]
                stratum.unit_weight_kn_m3 = st["unit_weight_kn_m3"]

    @staticmethod
    def auto_detect_province(lat: float, lon: float, strict: bool = True) -> IndianGeologicalProvince:
        """
        Automatically identifies the Indian Geological Province for a given (Latitude, Longitude) coordinate
        using nearest representative city centroids and regional domain constraints.

        Raises ValueError if strict is True and coordinates fall outside the geographic bounds
        of the Indian landmass (Latitude 6.0°N to 38.0°N, Longitude 68.0°E to 98.0°E).
        """
        if strict:
            if not (6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0):
                raise ValueError(
                    f"Coordinates ({lat:.4f}°N, {lon:.4f}°E) fall outside the geographic bounds "
                    f"of the Indian landmass (Latitude 6.0°N to 38.0°N, Longitude 68.0°E to 98.0°E)."
                )

        # 1. Bengal Delta & Coastal belt
        if 21.0 <= lat <= 23.5 and 87.0 <= lon <= 89.5:
            return IndianGeologicalProvince.COASTAL_DELTAIC

        # 2. Nearest representative city centroid across Indian geological domains
        best_province = IndianGeologicalProvince.INDO_GANGETIC_ALLUVIUM
        min_dist = float("inf")
        for prov, meta in PROVINCE_REGISTRY.items():
            for _, c_lat, c_lon in meta.typical_cities:
                d = (lat - c_lat)**2 + (lon - c_lon)**2
                if d < min_dist:
                    min_dist = d
                    best_province = prov
        return best_province

    @staticmethod
    def get_utm_epsg(lon: float, lat: float = 20.0) -> str:
        """Computes the appropriate WGS 84 / UTM Zone EPSG code for any longitude across India."""
        zone = int(math.floor((lon + 180.0) / 6.0) + 1)
        return f"EPSG:326{zone:02d}"

    def synthesize_site_dem(
        self,
        output_path: Path,
        province: IndianGeologicalProvince,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None,
        extent_m: float = 2000.0,
        resolution: float = 10.0,
        random_seed: Optional[int] = 42
    ) -> Tuple[np.ndarray, Affine, str, Path]:
        """
        Synthesizes a high-resolution, georeferenced GeoTIFF DEM raster for the target Indian site.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(random_seed)

        meta = self.province_metadata[province]
        if center_lat is None or center_lon is None:
            _, center_lat, center_lon = meta.typical_cities[0]

        crs_str = self.get_utm_epsg(center_lon, center_lat)

        # Reproject WGS84 center lat/lon to UTM meters
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", crs_str, always_xy=True)
        utm_easting, utm_northing = transformer.transform(center_lon, center_lat)

        nx = int(round(extent_m / resolution))
        ny = int(round(extent_m / resolution))

        x_origin = utm_easting - (extent_m / 2.0)
        y_origin = utm_northing + (extent_m / 2.0)

        transform = from_origin(x_origin, y_origin, resolution, resolution)
        dem_data = SpatialFieldSynthesizer.synthesize_terrain_dem(province, nx=nx, ny=ny, resolution=resolution, rng=rng)

        # Write GeoTIFF
        with rasterio.open(
            output_path,
            "w",
            driver="GTiff",
            height=ny,
            width=nx,
            count=1,
            dtype="float32",
            crs=CRS.from_string(crs_str),
            transform=transform,
            nodata=-9999.0,
        ) as dst:
            dst.write(dem_data, 1)

        return dem_data, transform, crs_str, output_path

    def synthesize_boreholes(
        self,
        province: IndianGeologicalProvince,
        num_boreholes: int = 15,
        dem_data: Optional[np.ndarray] = None,
        transform: Optional[Affine] = None,
        extent_bounds: Optional[Tuple[float, float, float, float]] = None,
        random_seed: Optional[int] = 42
    ) -> pd.DataFrame:
        """
        Generates realistic 3D geotechnical borehole drilling logs distributed across the site.
        Integrates Coupled Markov transition rules, spatially correlated layer thicknesses,
        stochastic pinch-outs, and depth-dependent IS:2131 SPT N-values.

        Returns:
            pd.DataFrame strictly conforming to the project's standard BoreholeProcessor schema.
        """
        rng = np.random.default_rng(random_seed)
        meta = self.province_metadata[province]
        strata_list = meta.strata
        num_strata = len(strata_list)

        # Setup coordinate grid bounds
        if dem_data is not None and transform is not None:
            ny, nx = dem_data.shape
            res_x, res_y = transform.a, -transform.e
            x_min, y_max = transform.c, transform.f
            x_max = x_min + nx * res_x
            y_min = y_max - ny * res_y
        elif extent_bounds is not None:
            x_min, y_min, x_max, y_max = extent_bounds
            res_x, res_y = 10.0, 10.0
            nx, ny = int((x_max - x_min) / 10.0), int((y_max - y_min) / 10.0)
            dem_data = np.full((ny, nx), (meta.elevation_range[0] + meta.elevation_range[1]) / 2.0, dtype=np.float32)
        else:
            x_min, y_min, x_max, y_max = 300000.0, 2300000.0, 302000.0, 2302000.0
            res_x, res_y = 10.0, 10.0
            nx, ny = 200, 200
            dem_data = np.full((ny, nx), (meta.elevation_range[0] + meta.elevation_range[1]) / 2.0, dtype=np.float32)

        # Distribute boreholes inside site perimeter (using 12% margin)
        margin_x = (x_max - x_min) * 0.12
        margin_y = (y_max - y_min) * 0.12

        eastings = rng.uniform(x_min + margin_x, x_max - margin_x, num_boreholes)
        northings = rng.uniform(y_min + margin_y, y_max - margin_y, num_boreholes)

        # Generate spatially continuous random fields for layer thickness modulation
        thickness_fields = [
            SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=30.0, rng=rng)
            for _ in range(num_strata)
        ]
        pinch_fields = [
            SpatialFieldSynthesizer.generate_gaussian_field(nx, ny, correlation_length_cells=20.0, rng=rng)
            for _ in range(num_strata)
        ]

        mean_site_dem = float(dem_data.mean())
        records = []

        for bh_i in range(num_boreholes):
            bh_id = f"BH-{bh_i + 1:02d}"
            easting = round(float(eastings[bh_i]), 2)
            northing = round(float(northings[bh_i]), 2)

            # Sample surface elevation from DEM
            c_idx = int(np.clip((easting - x_min) / res_x, 0, nx - 1))
            r_idx = int(np.clip((y_max - northing) / res_y, 0, ny - 1))
            surface_rl = round(float(dem_data[r_idx, c_idx]), 2)

            # Topography-correlated groundwater table depth
            elev_deviation = surface_rl - mean_site_dem
            wt_base = meta.water_table_depth_mean + 0.15 * elev_deviation + rng.normal(0, meta.water_table_depth_std * 0.5)
            water_table_depth = round(float(np.clip(wt_base, meta.water_table_depth_min, meta.water_table_depth_max)), 2)

            depth_cursor = 0.0

            for layer_idx, stratum in enumerate(strata_list, start=1):
                # Sample spatially correlated thickness
                t_field_val = thickness_fields[layer_idx - 1][r_idx, c_idx]
                pinch_val = pinch_fields[layer_idx - 1][r_idx, c_idx]

                # Lognormal thickness variation
                thick_sim = stratum.thickness_mean * math.exp(0.25 * t_field_val)
                thick_sim = max(stratum.min_thickness, thick_sim + rng.normal(0, stratum.thickness_std * 0.3))

                # Check for pinch-out (bedrock / refusal layer never pinches out)
                is_pinchout = False
                if stratum.pinchout_prob > 0.0 and not stratum.is_refusal and layer_idx < num_strata:
                    # Threshold on Gaussian field: P(Z < threshold) = pinchout_prob
                    from scipy.stats import norm
                    thresh = norm.ppf(stratum.pinchout_prob)
                    if pinch_val < thresh:
                        is_pinchout = True

                if is_pinchout:
                    records.append({
                        "Borehole_ID": bh_id,
                        "Easting_m": easting,
                        "Northing_m": northing,
                        "Surface_RL_m": surface_rl,
                        "Layer_Index": layer_idx,
                        "Layer_Name": stratum.name,
                        "Depth_From_m": round(depth_cursor, 2),
                        "Depth_To_m": round(depth_cursor, 2),
                        "Thickness_m": 0.0,
                        "Layer_Bottom_RL_m": round(surface_rl - depth_cursor, 2),
                        "Field_N": 0,
                        "Soil_Type": stratum.soil_type,
                        "Cohesion_kPa": stratum.cohesion_kpa,
                        "Friction_Angle_deg": stratum.friction_angle_deg,
                        "Unit_Weight_kN_m3": stratum.unit_weight_kn_m3,
                        "Water_Table_Depth_m": water_table_depth,
                        "Refusal_Reached": False,
                        "Is_Pinchout": True,
                    })
                else:
                    thick_round = round(float(thick_sim), 2)
                    depth_to = round(depth_cursor + thick_round, 2)
                    bottom_rl = round(surface_rl - depth_to, 2)
                    mid_depth = (depth_cursor + depth_to) / 2.0

                    # Depth-dependent SPT N-value
                    n_calc = stratum.field_n_mean + (stratum.n_depth_gradient * mid_depth) + rng.normal(0, stratum.field_n_std)
                    if stratum.is_refusal:
                        n_final = int(np.clip(round(n_calc), 50, 100))
                    else:
                        n_max = 80 if stratum.field_n_mean >= 40.0 else 49
                        n_final = int(np.clip(round(n_calc), 2, n_max))

                    records.append({
                        "Borehole_ID": bh_id,
                        "Easting_m": easting,
                        "Northing_m": northing,
                        "Surface_RL_m": surface_rl,
                        "Layer_Index": layer_idx,
                        "Layer_Name": stratum.name,
                        "Depth_From_m": round(depth_cursor, 2),
                        "Depth_To_m": depth_to,
                        "Thickness_m": thick_round,
                        "Layer_Bottom_RL_m": bottom_rl,
                        "Field_N": n_final,
                        "Soil_Type": stratum.soil_type,
                        "Cohesion_kPa": stratum.cohesion_kpa,
                        "Friction_Angle_deg": stratum.friction_angle_deg,
                        "Unit_Weight_kN_m3": stratum.unit_weight_kn_m3,
                        "Water_Table_Depth_m": water_table_depth,
                        "Refusal_Reached": stratum.is_refusal,
                        "Is_Pinchout": False,
                    })
                    depth_cursor = depth_to

        return pd.DataFrame(records)

    def synthesize_markov_cross_section(
        self,
        borehole_df: pd.DataFrame,
        strata_names: List[str],
        num_cols: int = 80,
        num_rows: int = 50,
        num_simulations: int = 8,
        k_values: Optional[List[float]] = None,
        random_seed: int = 42
    ) -> Dict:
        """
        Executes Coupled Markov Chain 2D cross-section simulation conditioned on synthesized/real boreholes,
        and computes the Shannon information entropy map to quantify geological uncertainty.
        """
        rng = np.random.default_rng(random_seed)
        num_states = len(strata_names)
        cmc = CoupledMarkovModel(num_states, k_values=k_values)

        # Discretize all borehole strata down depth columns for Markov vertical & horizontal transition training
        name_to_idx = {name.lower().strip(): idx for idx, name in enumerate(strata_names)}
        max_d_all = float(borehole_df["Depth_To_m"].max()) if "Depth_To_m" in borehole_df.columns and len(borehole_df) > 0 else 25.0
        train_dz = max_d_all / max(1, num_rows)

        discretized_training_sequences = []
        for _, grp in borehole_df.groupby("Borehole_ID"):
            bh_sorted = grp.sort_values(by="Depth_From_m" if "Depth_From_m" in grp.columns else "Depth_To_m")
            b_col = []
            for r in range(num_rows):
                cur_d = (r + 0.5) * train_dz
                matched = bh_sorted[(bh_sorted["Depth_From_m"] <= cur_d) & (bh_sorted["Depth_To_m"] >= cur_d)]
                if len(matched) > 0:
                    lname = matched.iloc[0]["Layer_Name"].lower().strip()
                    b_col.append(name_to_idx.get(lname, 0))
                else:
                    b_col.append(num_states - 1)
            discretized_training_sequences.append(b_col)

        cmc.fit_from_sequences(discretized_training_sequences)

        # Select 3-6 representative conditioning boreholes distributed evenly across the East-West transect
        bh_summary = borehole_df.groupby("Borehole_ID").agg({
            "Easting_m": "first",
            "Northing_m": "first",
            "Surface_RL_m": "first",
        }).sort_values(by="Easting_m")

        num_cond = min(5, len(bh_summary))
        indices = np.round(np.linspace(0, len(bh_summary) - 1, num_cond)).astype(int)
        selected_bhs = bh_summary.index[indices]
        cond_cols = []
        min_e = bh_summary.loc[selected_bhs, "Easting_m"].min()
        max_e = bh_summary.loc[selected_bhs, "Easting_m"].max()
        e_span = max(1.0, max_e - min_e)

        conditioning_grid = np.zeros((num_rows, len(selected_bhs)), dtype=np.int32)
        for i, bh_id in enumerate(selected_bhs):
            e_val = bh_summary.loc[bh_id, "Easting_m"]
            col_pos = int(np.clip(round(((e_val - min_e) / e_span) * (num_cols - 1)), 0, num_cols - 1))
            cond_cols.append(col_pos)

            # Discretize borehole strata down the column
            bh_rows = borehole_df[borehole_df["Borehole_ID"] == bh_id].sort_values(by="Depth_From_m")
            max_d = bh_rows["Depth_To_m"].max() if len(bh_rows) > 0 else 20.0
            depth_step = max_d / num_rows

            for r in range(num_rows):
                cur_d = (r + 0.5) * depth_step
                matched = bh_rows[(bh_rows["Depth_From_m"] <= cur_d) & (bh_rows["Depth_To_m"] >= cur_d)]
                if len(matched) > 0:
                    lname = matched.iloc[0]["Layer_Name"].lower().strip()
                    conditioning_grid[r, i] = name_to_idx.get(lname, 0)
                else:
                    conditioning_grid[r, i] = num_states - 1

        # Ensure column positions are strictly increasing and non-overlapping
        sorted_indices = np.argsort(cond_cols)
        sorted_cols = [cond_cols[k] for k in sorted_indices]
        for k in range(1, len(sorted_cols)):
            if sorted_cols[k] <= sorted_cols[k - 1]:
                sorted_cols[k] = sorted_cols[k - 1] + 1
        if sorted_cols[-1] >= num_cols:
            sorted_cols[-1] = num_cols - 1
            for k in range(len(sorted_cols) - 2, -1, -1):
                if sorted_cols[k] >= sorted_cols[k + 1]:
                    sorted_cols[k] = max(0, sorted_cols[k + 1] - 1)
        sorted_cond_grid = conditioning_grid[:, sorted_indices]

        # Run simulations
        realizations = []
        for _ in range(num_simulations):
            prof = cmc.simulate_2d_profile(
                conditioning_cols=sorted_cols,
                conditioning_layers=sorted_cond_grid,
                num_cols=num_cols,
                num_rows=num_rows,
                rng=rng
            )
            realizations.append(prof)

        prob_3d, entropy_grid = cmc.compute_information_entropy(realizations, num_states)

        return {
            "realizations": realizations,
            "probabilities": prob_3d,
            "entropy": entropy_grid,
            "conditioning_cols": sorted_cols,
            "strata_names": strata_names,
            "vertical_prob": cmc.vertical_prob,
            "horizontal_prob": cmc.horizontal_prob_1step,
        }

    def simulate_cmc_benchmark(
        self,
        cmc_dir: Optional[Union[str, Path]] = None,
        num_simulations: int = 8,
        random_seed: int = 1
    ) -> Dict:
        """
        Executes Coupled Markov Chain profile simulation directly against the CoupledMarkov
        example benchmark case (case_config.csv, soil_types.csv, boreholes.csv, borehole_layers.csv).
        """
        from src.config import PROJECT_ROOT
        if cmc_dir is None:
            cmc_dir = PROJECT_ROOT / "data/raw/CoupledMarkov/examples/boreholedata"
        cmc_dir = Path(cmc_dir)

        if not cmc_dir.exists():
            raise FileNotFoundError(f"CoupledMarkov example directory not found: {cmc_dir}")

        calib = GeotechnicalCalibrator.calibrate_from_cmc_boreholedata(cmc_dir)
        cfg = calib.get("config", {})
        num_soil_types = int(cfg.get("num_soil_types", len(calib["soil_types"])))
        k_values = calib.get("k_values", [12.4] * num_soil_types)
        num_cols = int(cfg.get("num_cols", 86))

        cmc = CoupledMarkovModel(num_states=num_soil_types, k_values=k_values)
        if len(calib["discretized_sequences"]) > 0:
            cmc.fit_from_sequences(calib["discretized_sequences"])

        bhs_df = pd.DataFrame(calib["boreholes"])
        cond_bhs = bhs_df[bhs_df["is_conditioning"] != 0].sort_values(by="grid_col")
        if len(cond_bhs) == 0:
            cond_bhs = bhs_df.sort_values(by="grid_col")

        cond_cols = [int(col) - 1 for col in cond_bhs["grid_col"]]  # convert 1-based to 0-based
        layers_df = pd.read_csv(cmc_dir / "borehole_layers.csv")
        depths = sorted(layers_df["depth_m"].unique())
        cond_grid = np.zeros((len(depths), len(cond_bhs)), dtype=np.int32)
        for i, bh_id in enumerate(cond_bhs["borehole_id"]):
            bh_l = layers_df[layers_df["borehole_id"] == bh_id].sort_values(by="depth_m")
            for r, d_val in enumerate(depths):
                match = bh_l[bh_l["depth_m"] == d_val]
                if len(match) > 0:
                    cond_grid[r, i] = int(match.iloc[0]["layer_id"]) - 1
                else:
                    cond_grid[r, i] = 0

        rng = np.random.default_rng(random_seed)
        realizations = []
        for _ in range(num_simulations):
            prof = cmc.simulate_2d_profile(
                conditioning_cols=cond_cols,
                conditioning_layers=cond_grid,
                num_cols=num_cols,
                num_rows=len(depths),
                rng=rng
            )
            realizations.append(prof)

        prob_3d, entropy = cmc.compute_information_entropy(realizations, num_soil_types)

        return {
            "realizations": realizations,
            "probabilities": prob_3d,
            "entropy": entropy,
            "conditioning_cols": cond_cols,
            "soil_types": calib["soil_types"],
            "k_values": k_values,
            "vertical_prob": cmc.vertical_prob,
            "horizontal_prob": cmc.horizontal_prob_1step,
        }

