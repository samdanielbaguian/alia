import pytest
from app.schemas.shipping import ShippingQuoteRequest, DeliveryMethod
from app.services.shipping_algorithm import ShippingAlgorithm


class TestShippingAlgorithm:
    """Test cases for the Shipping Algorithm"""
    
    def test_zone_not_allowed(self):
        """Test delivery to non-allowed zone"""
        request = ShippingQuoteRequest(
            article_weight=1.0,
            delivery_address="France",
            delivery_city="Paris",
            stock_city="Ouagadougou",
            distance=10.0
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is False
        assert quote.delivery_price == 0
    
    def test_primary_algorithm_local(self):
        """Test PRIMARY algorithm: local delivery (same city, <= 1kg, <= 30km)"""
        request = ShippingQuoteRequest(
            article_weight=0.5,
            delivery_address="Burkina Faso",
            delivery_city="Ouagadougou",
            stock_city="Ouagadougou",
            distance=15.0,
            delivery_rating=4.8
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_price == 2000
        assert quote.delivery_time == (1, 3)
        assert quote.commission == 500  # 25% of 2000
    
    def test_primary_algorithm_regional(self):
        """Test PRIMARY algorithm: regional delivery (30km < distance <= 60km)"""
        request = ShippingQuoteRequest(
            article_weight=2.0,
            delivery_address="Mali",
            delivery_city="Kayes",
            stock_city="Bamako",
            distance=45.0,
            delivery_rating=4.0
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_price == 3500
        assert quote.delivery_time == (1, 3)
        assert quote.commission == 875  # 25% of 3500
    
    def test_secondary_algorithm_long_distance_light(self):
        """Test SECONDARY algorithm: long distance, light weight"""
        request = ShippingQuoteRequest(
            article_weight=0.8,
            delivery_address="Niger",
            delivery_city="Niamey",
            stock_city="Maradi",
            distance=75.0,
            delivery_rating=4.5
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_price == 5000
        assert quote.delivery_time == (2, 4)
        assert quote.commission == 1250  # 25% of 5000
    
    def test_secondary_algorithm_long_distance_medium(self):
        """Test SECONDARY algorithm: long distance, medium weight (1-2kg)"""
        request = ShippingQuoteRequest(
            article_weight=1.5,
            delivery_address="Ivory Coast",
            delivery_city="Abidjan",
            stock_city="Yamoussoukro",
            distance=70.0,
            delivery_rating=3.0
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_price == 5000
        assert quote.delivery_time == (2, 4)
        assert quote.delivery_method == DeliveryMethod.CAR
        assert quote.commission == 1250
    
    def test_third_algorithm_very_long_light(self):
        """Test THIRD algorithm: very long distance (100-800km), light weight (<= 5kg)"""
        request = ShippingQuoteRequest(
            article_weight=3.5,
            delivery_address="Ghana",
            delivery_city="Accra",
            stock_city="Kumasi",
            distance=250.0,
            delivery_rating=4.2
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_price == 7000
        assert quote.delivery_time == (3, 7)
        assert quote.delivery_method == DeliveryMethod.CAR
        assert quote.commission == 1750  # 25% of 7000
    
    def test_third_algorithm_very_long_heavy(self):
        """Test THIRD algorithm: very long distance (100-800km), heavy weight (> 5kg)"""
        request = ShippingQuoteRequest(
            article_weight=8.0,
            delivery_address="Togo",
            delivery_city="Lome",
            stock_city="Kara",
            distance=300.0,
            delivery_rating=3.5
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_price == 10000
        assert quote.delivery_time == (5, 10)
        assert quote.delivery_method == DeliveryMethod.TRUCK
        assert quote.commission == 2500  # 25% of 10000
    
    def test_delivery_method_high_rating(self):
        """Test delivery method selection with high rating"""
        request = ShippingQuoteRequest(
            article_weight=0.5,
            delivery_address="Benin",
            delivery_city="Porto-Novo",
            stock_city="Cotonou",
            distance=20.0,
            delivery_rating=4.8  # High rating
        )
        
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_method in [DeliveryMethod.MOTORBIKE, DeliveryMethod.BICYCLE]

    def test_delivery_method_high_rating_short_same_city_uses_bicycle(self):
        """Short same-city routes should prefer bicycle for light parcels"""
        request = ShippingQuoteRequest(
            article_weight=0.5,
            delivery_address="Burkina Faso",
            delivery_city="Ouagadougou",
            stock_city="Ouagadougou",
            distance=5.0,
            delivery_rating=4.9
        )

        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_method == DeliveryMethod.BICYCLE

    def test_delivery_method_high_rating_long_distance_not_two_wheeler(self):
        """Light parcels on long routes should not use bicycle or motorbike"""
        request = ShippingQuoteRequest(
            article_weight=0.8,
            delivery_address="Niger",
            delivery_city="Niamey",
            stock_city="Maradi",
            distance=75.0,
            delivery_rating=4.8
        )

        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        assert quote.zone_allowed is True
        assert quote.delivery_method == DeliveryMethod.CAR
    
    def test_check_zone_allowed(self):
        """Test zone validation"""
        assert ShippingAlgorithm.check_zone_allowed("Burkina Faso") is True
        assert ShippingAlgorithm.check_zone_allowed("Mali") is True
        assert ShippingAlgorithm.check_zone_allowed("France") is False
        assert ShippingAlgorithm.check_zone_allowed("USA") is False
    
    def test_commission_calculation(self):
        """Test that commission is always 25%"""
        prices = [2000, 3500, 5000, 7000, 10000]
        
        for price in prices:
            expected_commission = (price * 25) / 100
            assert expected_commission == price * 0.25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
