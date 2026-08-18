"""
Property Value Engine for Akiya Scout
Calculates Akiya Score (0-100), estimated renovation cost, and total cost.
Provides transparent breakdown of scoring.
"""
import logging
import math
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from app.models import Property

logger = logging.getLogger(__name__)


@dataclass
class ValuationConfig:
    """Configuration for property valuation rules."""
    # Score weights (must sum to 100)
    price_weight: float = 20.0
    land_weight: float = 15.0
    building_weight: float = 10.0
    age_weight: float = 15.0
    accessibility_weight: float = 10.0
    data_confidence_weight: float = 10.0
    rooms_weight: float = 10.0
    parking_weight: float = 10.0
    
    # Price thresholds (in yen)
    excellent_price: int = 3000000  # Below this is excellent
    good_price: int = 5000000      # Below this is good
    fair_price: int = 10000000     # Below this is fair
    
    # Land size thresholds (in m²)
    large_land: float = 300.0      # Above this is excellent
    good_land: float = 200.0       # Above this is good
    fair_land: float = 100.0       # Above this is fair
    
    # Building size thresholds (in m²)
    large_building: float = 150.0   # Above this is excellent
    good_building: float = 100.0    # Above this is good
    fair_building: float = 50.0     # Above this is fair
    
    # Building age thresholds (in years)
    new_building: int = 20          # Below this is excellent
    moderate_building: int = 35     # Below this is good
    old_building: int = 50          # Below this is fair
    
    # Renovation cost per m² based on age
    renovation_cost_new: float = 30000      # per m² for new buildings
    renovation_cost_moderate: float = 50000  # per m² for moderate age
    renovation_cost_old: float = 80000       # per m² for old buildings
    renovation_cost_unknown: float = 60000   # per m² when age unknown
    
    # Minimum renovation cost
    min_renovation_cost: int = 500000
    max_renovation_cost: int = 20000000


@dataclass
class ScoreBreakdown:
    """Breakdown of individual scores."""
    category: str
    score: float
    max_score: float
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "explanation": self.explanation
        }


@dataclass
class ValuationResult:
    """Complete valuation result."""
    akiya_score: float
    estimated_renovation_cost: int
    estimated_total_cost: int
    breakdown: List[ScoreBreakdown]
    disclaimer: str = "This is not a professional real-estate estimate. Scores are calculated using simple configurable rules for comparison purposes only."
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "akiya_score": round(self.akiya_score, 2),
            "estimated_renovation_cost": self.estimated_renovation_cost,
            "estimated_total_cost": self.estimated_total_cost,
            "breakdown": [b.to_dict() for b in self.breakdown],
            "disclaimer": self.disclaimer
        }


class PropertyValuationEngine:
    """
    Engine for calculating property value scores.
    Provides transparent scoring with configurable rules.
    """
    
    def __init__(self, config: Optional[ValuationConfig] = None):
        """
        Initialize valuation engine.
        
        Args:
            config: Optional custom configuration
        """
        self.config = config or ValuationConfig()
    
    def calculate_renovation_cost(self, property_obj: Property) -> int:
        """
        Calculate estimated renovation cost based on building size and age.
        
        Args:
            property_obj: Property to evaluate
            
        Returns:
            Estimated renovation cost in yen
        """
        if property_obj.building_size_m2 is None:
            # If we don't know building size, use a conservative estimate
            return self.config.min_renovation_cost
        
        building_size = property_obj.building_size_m2
        
        # Determine renovation cost per m² based on age
        if property_obj.build_year is None:
            cost_per_m2 = self.config.renovation_cost_unknown
        else:
            current_year = 2026  # Current year (can be made dynamic)
            building_age = current_year - property_obj.build_year
            
            if building_age <= self.config.new_building:
                cost_per_m2 = self.config.renovation_cost_new
            elif building_age <= self.config.moderate_building:
                cost_per_m2 = self.config.renovation_cost_moderate
            else:
                cost_per_m2 = self.config.renovation_cost_old
        
        # Calculate total renovation cost
        renovation_cost = building_size * cost_per_m2
        
        # Apply min/max bounds
        renovation_cost = max(renovation_cost, self.config.min_renovation_cost)
        renovation_cost = min(renovation_cost, self.config.max_renovation_cost)
        
        return int(renovation_cost)
    
    def calculate_total_cost(self, property_obj: Property, renovation_cost: int) -> Optional[int]:
        """
        Calculate estimated total cost (purchase price + renovation).
        
        Args:
            property_obj: Property to evaluate
            renovation_cost: Estimated renovation cost
            
        Returns:
            Total cost in yen, or None if purchase price is unknown
        """
        if property_obj.price is None:
            return None
        
        return property_obj.price + renovation_cost
    
    def score_price(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on purchase price."""
        max_score = self.config.price_weight
        
        if property_obj.price is None:
            return ScoreBreakdown(
                "Price value", 0, max_score,
                "No price information available"
            )
        
        price = property_obj.price
        
        if price <= self.config.excellent_price:
            score = max_score
            explanation = f"Excellent price ({price:,} yen)"
        elif price <= self.config.good_price:
            score = max_score * 0.8
            explanation = f"Good price ({price:,} yen)"
        elif price <= self.config.fair_price:
            score = max_score * 0.6
            explanation = f"Fair price ({price:,} yen)"
        else:
            score = max_score * 0.4
            explanation = f"Above average price ({price:,} yen)"
        
        return ScoreBreakdown("Price value", score, max_score, explanation)
    
    def score_land(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on land size."""
        max_score = self.config.land_weight
        
        if property_obj.land_size_m2 is None:
            return ScoreBreakdown(
                "Land value", 0, max_score,
                "No land size information available"
            )
        
        land_size = property_obj.land_size_m2
        
        if land_size >= self.config.large_land:
            score = max_score
            explanation = f"Large land ({land_size:.1f} m²)"
        elif land_size >= self.config.good_land:
            score = max_score * 0.8
            explanation = f"Good land size ({land_size:.1f} m²)"
        elif land_size >= self.config.fair_land:
            score = max_score * 0.6
            explanation = f"Fair land size ({land_size:.1f} m²)"
        else:
            score = max_score * 0.3
            explanation = f"Small land ({land_size:.1f} m²)"
        
        return ScoreBreakdown("Land value", score, max_score, explanation)
    
    def score_building(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on building size."""
        max_score = self.config.building_weight
        
        if property_obj.building_size_m2 is None:
            return ScoreBreakdown(
                "Building value", 0, max_score,
                "No building size information available"
            )
        
        building_size = property_obj.building_size_m2
        
        if building_size >= self.config.large_building:
            score = max_score
            explanation = f"Large building ({building_size:.1f} m²)"
        elif building_size >= self.config.good_building:
            score = max_score * 0.8
            explanation = f"Good building size ({building_size:.1f} m²)"
        elif building_size >= self.config.fair_building:
            score = max_score * 0.6
            explanation = f"Fair building size ({building_size:.1f} m²)"
        else:
            score = max_score * 0.3
            explanation = f"Small building ({building_size:.1f} m²)"
        
        return ScoreBreakdown("Building value", score, max_score, explanation)
    
    def score_age(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on building age."""
        max_score = self.config.age_weight
        
        if property_obj.build_year is None:
            return ScoreBreakdown(
                "Age", 0, max_score,
                "No build year information available"
            )
        
        current_year = 2026  # Can be made dynamic
        building_age = current_year - property_obj.build_year
        
        if building_age < 0:
            # Future build year (invalid data)
            return ScoreBreakdown(
                "Age", 0, max_score,
                f"Invalid build year ({property_obj.build_year})"
            )
        
        if building_age <= self.config.new_building:
            score = max_score
            explanation = f"Relatively new ({building_age} years old)"
        elif building_age <= self.config.moderate_building:
            score = max_score * 0.7
            explanation = f"Moderate age ({building_age} years old)"
        elif building_age <= self.config.old_building:
            score = max_score * 0.5
            explanation = f"Older building ({building_age} years old)"
        else:
            score = max_score * 0.3
            explanation = f"Very old building ({building_age} years old)"
        
        return ScoreBreakdown("Age", score, max_score, explanation)
    
    def score_accessibility(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on available location/accessibility info."""
        max_score = self.config.accessibility_weight
        
        score = 0
        factors = []
        
        # Check for location info
        if property_obj.prefecture is not None:
            score += max_score * 0.3
            factors.append(f"Prefecture: {property_obj.prefecture}")
        
        if property_obj.municipality is not None:
            score += max_score * 0.3
            factors.append(f"Municipality: {property_obj.municipality}")
        
        if property_obj.area is not None:
            score += max_score * 0.2
            factors.append(f"Area: {property_obj.area}")
        
        if property_obj.latitude is not None and property_obj.longitude is not None:
            score += max_score * 0.2
            factors.append("Coordinates available")
        
        if not factors:
            explanation = "No location information available"
        else:
            explanation = ", ".join(factors)
        
        return ScoreBreakdown("Accessibility", score, max_score, explanation)
    
    def score_data_confidence(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on completeness of property information."""
        max_score = self.config.data_confidence_weight
        
        # Count available fields
        available_fields = 0
        total_fields = 12  # Total number of optional fields we consider
        
        if property_obj.price is not None:
            available_fields += 1
        if property_obj.land_size_m2 is not None:
            available_fields += 1
        if property_obj.building_size_m2 is not None:
            available_fields += 1
        if property_obj.build_year is not None:
            available_fields += 1
        if property_obj.rooms is not None:
            available_fields += 1
        if property_obj.structure is not None:
            available_fields += 1
        if property_obj.floors is not None:
            available_fields += 1
        if property_obj.parking is not None:
            available_fields += 1
        if property_obj.description is not None:
            available_fields += 1
        if property_obj.image_url is not None:
            available_fields += 1
        if property_obj.latitude is not None:
            available_fields += 1
        if property_obj.longitude is not None:
            available_fields += 1
        
        score = (available_fields / total_fields) * max_score
        explanation = f"{available_fields}/{total_fields} data fields available"
        
        return ScoreBreakdown("Data confidence", score, max_score, explanation)
    
    def score_rooms(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on number of rooms."""
        max_score = self.config.rooms_weight
        
        if property_obj.rooms is None:
            return ScoreBreakdown(
                "Rooms", 0, max_score,
                "No room information available"
            )
        
        # Extract room count
        import re
        match = re.match(r'(\d+)', property_obj.rooms)
        
        if match is None:
            return ScoreBreakdown(
                "Rooms", max_score * 0.5, max_score,
                f"Room layout: {property_obj.rooms}"
            )
        
        room_count = int(match.group(1))
        
        if room_count >= 4:
            score = max_score
            explanation = f"Spacious ({room_count} rooms)"
        elif room_count >= 3:
            score = max_score * 0.8
            explanation = f"Good size ({room_count} rooms)"
        elif room_count >= 2:
            score = max_score * 0.6
            explanation = f"Compact ({room_count} rooms)"
        else:
            score = max_score * 0.4
            explanation = f"Small ({room_count} rooms)"
        
        return ScoreBreakdown("Rooms", score, max_score, explanation)
    
    def score_parking(self, property_obj: Property) -> ScoreBreakdown:
        """Score based on parking availability."""
        max_score = self.config.parking_weight
        
        if property_obj.parking is None:
            return ScoreBreakdown(
                "Parking", 0, max_score,
                "No parking information available"
            )
        
        parking = property_obj.parking
        
        if 'なし' in parking or 'none' in parking.lower() or 'no' in parking.lower():
            score = max_score * 0.3
            explanation = f"No parking ({parking})"
        elif 'あり' in parking or 'available' in parking.lower() or 'yes' in parking.lower():
            score = max_score
            explanation = f"Parking available ({parking})"
        else:
            score = max_score * 0.6
            explanation = f"Parking info: {parking}"
        
        return ScoreBreakdown("Parking", score, max_score, explanation)
    
    def valuate(self, property_obj: Property) -> ValuationResult:
        """
        Calculate complete valuation for a property.
        
        Args:
            property_obj: Property to evaluate
            
        Returns:
            ValuationResult with score, costs, and breakdown
        """
        # Calculate all scores
        breakdown = [
            self.score_price(property_obj),
            self.score_land(property_obj),
            self.score_building(property_obj),
            self.score_age(property_obj),
            self.score_accessibility(property_obj),
            self.score_data_confidence(property_obj),
            self.score_rooms(property_obj),
            self.score_parking(property_obj),
        ]
        
        # Calculate total score
        total_score = sum(b.score for b in breakdown)
        
        # Calculate renovation cost
        renovation_cost = self.calculate_renovation_cost(property_obj)
        
        # Calculate total cost
        total_cost = self.calculate_total_cost(property_obj, renovation_cost)
        
        return ValuationResult(
            akiya_score=total_score,
            estimated_renovation_cost=renovation_cost,
            estimated_total_cost=total_cost if total_cost is not None else 0,
            breakdown=breakdown
        )


# Global valuation engine instance
valuation_engine = PropertyValuationEngine()