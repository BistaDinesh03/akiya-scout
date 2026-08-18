"""
Tests for Property Valuation Engine
"""
import pytest
from datetime import datetime
from app.services.valuation import (
    PropertyValuationEngine,
    ValuationConfig,
    ValuationResult,
    ScoreBreakdown,
    valuation_engine
)
from app.models import Property


def create_test_property(**kwargs):
    """Helper to create test Property objects."""
    defaults = {
        'id': 'val-test-1',
        'title': 'Test Property',
        'price': 5000000,
        'prefecture': 'Saga',
        'municipality': 'Takeo',
        'area': 'Test Area',
        'land_size_m2': 200.0,
        'building_size_m2': 100.0,
        'build_year': 1990,
        'rooms': '3LDK',
        'structure': 'Wooden',
        'floors': 2,
        'parking': 'あり',
        'description': 'Test description',
        'source_name': 'test_source',
        'source_url': 'https://example.com/test',
        'image_url': 'https://example.com/image.jpg',
        'latitude': 33.1905,
        'longitude': 130.0209,
    }
    defaults.update(kwargs)
    return Property(**defaults)


class TestRenovationCost:
    """Test renovation cost calculation."""
    
    def test_renovation_cost_based_on_building_size(self):
        """Test that larger buildings cost more to renovate."""
        engine = PropertyValuationEngine()
        
        small = create_test_property(id="small", building_size_m2=50.0)
        large = create_test_property(id="large", building_size_m2=200.0)
        
        small_cost = engine.calculate_renovation_cost(small)
        large_cost = engine.calculate_renovation_cost(large)
        
        assert large_cost > small_cost
    
    def test_renovation_cost_based_on_age(self):
        """Test that older buildings cost more to renovate."""
        engine = PropertyValuationEngine()
        
        new = create_test_property(id="new", building_size_m2=100.0, build_year=2020)
        old = create_test_property(id="old", building_size_m2=100.0, build_year=1970)
        
        new_cost = engine.calculate_renovation_cost(new)
        old_cost = engine.calculate_renovation_cost(old)
        
        assert old_cost > new_cost
    
    def test_renovation_cost_minimum(self):
        """Test that renovation cost has a minimum."""
        engine = PropertyValuationEngine()
        
        tiny = create_test_property(id="tiny", building_size_m2=5.0)
        cost = engine.calculate_renovation_cost(tiny)
        
        assert cost >= engine.config.min_renovation_cost
    
    def test_renovation_cost_without_building_size(self):
        """Test renovation cost when building size unknown."""
        engine = PropertyValuationEngine()
        
        no_size = create_test_property(id="no-size", building_size_m2=None)
        cost = engine.calculate_renovation_cost(no_size)
        
        assert cost == engine.config.min_renovation_cost
    
    def test_renovation_cost_without_build_year(self):
        """Test renovation cost when build year unknown."""
        engine = PropertyValuationEngine()
        
        no_year = create_test_property(id="no-year", building_size_m2=100.0, build_year=None)
        cost = engine.calculate_renovation_cost(no_year)
        
        # Should use unknown age rate
        expected = 100.0 * engine.config.renovation_cost_unknown
        assert cost == expected


class TestTotalCost:
    """Test total cost calculation."""
    
    def test_total_cost_includes_renovation(self):
        """Test that total cost = price + renovation."""
        engine = PropertyValuationEngine()
        
        prop = create_test_property(price=5000000, building_size_m2=100.0, build_year=1990)
        renovation = engine.calculate_renovation_cost(prop)
        total = engine.calculate_total_cost(prop, renovation)
        
        assert total == 5000000 + renovation
    
    def test_total_cost_without_price(self):
        """Test total cost when price unknown."""
        engine = PropertyValuationEngine()
        
        prop = create_test_property(price=None)
        renovation = 1000000
        total = engine.calculate_total_cost(prop, renovation)
        
        assert total is None


class TestScoring:
    """Test individual score calculations."""
    
    def test_score_price_excellent(self):
        """Test excellent price score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(price=2000000)
        
        score = engine.score_price(prop)
        assert score.score == score.max_score
        assert score.score > 0
    
    def test_score_price_missing(self):
        """Test missing price score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(price=None)
        
        score = engine.score_price(prop)
        assert score.score == 0
    
    def test_score_land_excellent(self):
        """Test excellent land score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(land_size_m2=400.0)
        
        score = engine.score_land(prop)
        assert score.score == score.max_score
    
    def test_score_land_missing(self):
        """Test missing land score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(land_size_m2=None)
        
        score = engine.score_land(prop)
        assert score.score == 0
    
    def test_score_age_missing(self):
        """Test missing age score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(build_year=None)
        
        score = engine.score_age(prop)
        assert score.score == 0
    
    def test_score_age_invalid(self):
        """Test invalid age (future year)."""
        engine = PropertyValuationEngine()
        prop = create_test_property(build_year=2030)
        
        score = engine.score_age(prop)
        assert score.score == 0
    
    def test_score_data_confidence_full(self):
        """Test data confidence with all fields."""
        engine = PropertyValuationEngine()
        prop = create_test_property()
        
        score = engine.score_data_confidence(prop)
        assert score.score > 0
        assert score.score <= score.max_score
    
    def test_score_rooms_missing(self):
        """Test missing rooms score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(rooms=None)
        
        score = engine.score_rooms(prop)
        assert score.score == 0
    
    def test_score_parking_missing(self):
        """Test missing parking score."""
        engine = PropertyValuationEngine()
        prop = create_test_property(parking=None)
        
        score = engine.score_parking(prop)
        assert score.score == 0


class TestValuation:
    """Test complete valuation."""
    
    def test_valuate_returns_result(self):
        """Test that valuate returns ValuationResult."""
        engine = PropertyValuationEngine()
        prop = create_test_property()
        
        result = engine.valuate(prop)
        
        assert isinstance(result, ValuationResult)
        assert result.akiya_score > 0
        assert result.akiya_score <= 100
        assert result.estimated_renovation_cost > 0
        assert result.estimated_total_cost > 0
        assert len(result.breakdown) == 8
    
    def test_valuate_score_range(self):
        """Test that score is always between 0 and 100."""
        engine = PropertyValuationEngine()
        
        # Test various properties
        test_cases = [
            create_test_property(id="full", price=2000000, land_size_m2=400.0, building_size_m2=200.0, build_year=2020),
            create_test_property(id="partial", price=5000000, land_size_m2=150.0, building_size_m2=80.0, build_year=1980),
            create_test_property(id="minimal", price=None, land_size_m2=None, building_size_m2=None, build_year=None, rooms=None, parking=None),
        ]
        
        for prop in test_cases:
            result = engine.valuate(prop)
            assert 0 <= result.akiya_score <= 100
            assert len(result.breakdown) == 8
    
    def test_valuate_breakdown_explanations(self):
        """Test that breakdown has explanations."""
        engine = PropertyValuationEngine()
        prop = create_test_property()
        
        result = engine.valuate(prop)
        
        for breakdown in result.breakdown:
            assert isinstance(breakdown, ScoreBreakdown)
            assert breakdown.category is not None
            assert breakdown.explanation is not None
            assert breakdown.max_score > 0
            assert 0 <= breakdown.score <= breakdown.max_score
    
    def test_valuate_to_dict(self):
        """Test that result can be converted to dict."""
        engine = PropertyValuationEngine()
        prop = create_test_property()
        
        result = engine.valuate(prop)
        result_dict = result.to_dict()
        
        assert "akiya_score" in result_dict
        assert "estimated_renovation_cost" in result_dict
        assert "estimated_total_cost" in result_dict
        assert "breakdown" in result_dict
        assert "disclaimer" in result_dict
        assert len(result_dict["breakdown"]) == 8
    
    def test_valuate_disclaimer(self):
        """Test that disclaimer is included."""
        engine = PropertyValuationEngine()
        prop = create_test_property()
        
        result = engine.valuate(prop)
        
        assert "not a professional real-estate estimate" in result.disclaimer.lower()


class TestConfigurableRules:
    """Test that rules are configurable."""
    
    def test_custom_config(self):
        """Test that custom config changes scoring."""
        default_engine = PropertyValuationEngine()
        custom_config = ValuationConfig(
            excellent_price=1000000,
            good_price=2000000,
            fair_price=3000000,
        )
        custom_engine = PropertyValuationEngine(custom_config)
        
        prop = create_test_property(price=1500000)
        
        default_score = default_engine.score_price(prop)
        custom_score = custom_engine.score_price(prop)
        
        # Custom config should give different score for same price
        assert default_score.score != custom_score.score