"""Enhanced estimation service for shipping, labor, and project costs"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import os
import logging
from uuid import UUID
import psycopg2

from packages.schemas.estimation import (
    ShippingEstimateRequest, ShippingEstimate, ShippingMethod,
    LaborEstimateRequest, LaborEstimate, LaborRole,
    ProjectEstimateRequest, ProjectEstimate,
    MaterialRequirement, RateCardUpdate, ShippingQuoteCreate
)
from services.pricing_resolver import pricing_resolver
from services.observability_service import observability_service

logger = logging.getLogger(__name__)

class EstimationService:
    """Service for comprehensive cost estimation"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        
        # Default shipping rates (NIS)
        self.shipping_rates = {
            ShippingMethod.STANDARD: {
                'base_fee': 50.0,
                'per_km': 2.0,
                'per_kg': 5.0,
                'min_days': 3.0,
                'max_days': 7.0
            },
            ShippingMethod.EXPRESS: {
                'base_fee': 100.0,
                'per_km': 3.0,
                'per_kg': 8.0,
                'min_days': 1.0,
                'max_days': 3.0
            },
            ShippingMethod.FREIGHT: {
                'base_fee': 200.0,
                'per_km': 1.5,
                'per_kg': 3.0,
                'min_days': 5.0,
                'max_days': 14.0
            },
            ShippingMethod.LOCAL: {
                'base_fee': 30.0,
                'per_km': 1.0,
                'per_kg': 2.0,
                'min_days': 1.0,
                'max_days': 2.0
            }
        }
        
        # Default labor efficiency factors
        self.labor_efficiency = {
            LaborRole.CARPENTER: 0.9,
            LaborRole.PAINTER: 0.8,
            LaborRole.ELECTRICIAN: 0.85,
            LaborRole.PLUMBER: 0.85,
            LaborRole.LABORER: 1.0,
            LaborRole.PROJECT_MANAGER: 0.95,
            LaborRole.DESIGNER: 0.9,
            LaborRole.INSTALLER: 0.88
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def estimate_shipping(self, request: ShippingEstimateRequest) -> ShippingEstimate:
        """Estimate shipping costs with enhanced model"""
        import time
        start_time = time.time()
        
        try:
            # Try to get historical quotes first
            historical_quote = self._get_historical_shipping_quote(request)
            if historical_quote:
                return self._create_estimate_from_historical(request, historical_quote)
            
            # Use default rates with enhancements
            rates = self.shipping_rates[request.method]
            
            base_cost = rates['base_fee']
            distance_cost = request.distance_km * rates['per_km']
            weight_cost = request.weight_kg * rates['per_kg']
            
            # Apply surcharges
            urgency_surcharge = base_cost * (request.urgency - 1.0) * 0.5
            fragile_surcharge = base_cost * 0.15 if request.fragile else 0.0
            
            # Insurance cost (0.5% of value)
            insurance_cost = request.insurance_value * 0.005 if request.insurance_value else 0.0
            
            total_cost = base_cost + distance_cost + weight_cost + urgency_surcharge + fragile_surcharge + insurance_cost
            
            # Estimate delivery time
            avg_speed = 50.0  # km/h
            driving_hours = request.distance_km / avg_speed
            processing_days = rates['min_days'] if request.method == ShippingMethod.EXPRESS else rates['min_days'] + 1
            estimated_days = processing_days + (driving_hours / 8.0)  # 8 driving hours per day
            
            # Adjust for express shipping
            if request.method == ShippingMethod.EXPRESS:
                estimated_days = max(1.0, min(estimated_days, rates['max_days']))
            else:
                estimated_days = max(rates['min_days'], min(estimated_days, rates['max_days']))
            
            confidence = 0.8 if historical_quote else 0.7
            
            result = ShippingEstimate(
                base_cost=base_cost,
                distance_cost=distance_cost,
                weight_cost=weight_cost,
                urgency_surcharge=urgency_surcharge,
                fragile_surcharge=fragile_surcharge,
                insurance_cost=insurance_cost,
                total_cost=round(total_cost, 2),
                confidence=confidence,
                estimated_days=round(estimated_days, 1),
                method=request.method,
                notes="Based on standard rates with surcharges applied"
            )
            
            # Track successful estimation
            if observability_service.enabled:
                duration_ms = (time.time() - start_time) * 1000
                observability_service.track_estimation(
                    trace_id=observability_service.get_current_trace_id(),
                    estimation_type="shipping",
                    request=request.dict(),
                    response=result.dict(),
                    confidence=confidence,
                    duration_ms=duration_ms
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Shipping estimation error: {e}")
            
            # Track estimation error
            if observability_service.enabled:
                duration_ms = (time.time() - start_time) * 1000
                observability_service.track_error(
                    trace_id=observability_service.get_current_trace_id(),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={
                        'estimation_type': 'shipping',
                        'duration_ms': duration_ms,
                        'request': request.dict()
                    }
                )
            
            # Fallback to simple pricing resolver
            simple_estimate = pricing_resolver.estimate_shipping_cost(request.weight_kg, request.distance_km)
            return ShippingEstimate(
                base_cost=simple_estimate['base_fee'],
                distance_cost=request.distance_km * simple_estimate['per_km_rate'],
                weight_cost=request.weight_kg * simple_estimate['per_kg_rate'],
                total_cost=simple_estimate['estimated_cost'],
                confidence=simple_estimate['confidence'],
                estimated_days=7.0,  # Default
                method=request.method,
                notes="Fallback estimate using basic pricing resolver"
            )
    
    def _get_historical_shipping_quote(self, request: ShippingEstimateRequest) -> Optional[Dict[str, Any]]:
        """Get historical shipping quote for similar parameters"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT base_fee_nis, per_km_nis, per_kg_nis, distance_km, weight_kg, type, confidence
                    FROM shipping_quotes 
                    WHERE type = %s 
                    AND distance_km BETWEEN %s AND %s
                    AND weight_kg BETWEEN %s AND %s
                    ORDER BY confidence DESC, fetched_at DESC
                    LIMIT 1
                """, (
                    request.method.value,
                    request.distance_km * 0.8,  # 20% range
                    request.distance_km * 1.2,
                    request.weight_kg * 0.8,
                    request.weight_kg * 1.2
                ))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'base_fee': float(result[0]),
                        'per_km': float(result[1]),
                        'per_kg': float(result[2]),
                        'distance': float(result[3]),
                        'weight': float(result[4]),
                        'method': result[5],
                        'confidence': float(result[6])
                    }
            return None
        except Exception as e:
            logger.warning(f"Error fetching historical shipping quotes: {e}")
            return None
        finally:
            conn.close()
    
    def _create_estimate_from_historical(self, request: ShippingEstimateRequest, historical: Dict[str, Any]) -> ShippingEstimate:
        """Create estimate based on historical data"""
        base_cost = historical['base_fee']
        distance_cost = request.distance_km * historical['per_km']
        weight_cost = request.weight_kg * historical['per_kg']
        
        # Adjust for differences from historical quote
        distance_ratio = request.distance_km / historical['distance'] if historical['distance'] > 0 else 1.0
        weight_ratio = request.weight_kg / historical['weight'] if historical['weight'] > 0 else 1.0
        
        # Apply non-linear scaling for large differences
        if distance_ratio > 1.5:
            distance_cost *= 1.1  # 10% surcharge for much longer distances
        if weight_ratio > 2.0:
            weight_cost *= 1.15  # 15% surcharge for much heavier shipments
        
        total_cost = base_cost + distance_cost + weight_cost
        
        # Estimate delivery time based on method
        if request.method == ShippingMethod.EXPRESS:
            estimated_days = max(1.0, min(5.0, request.distance_km / 500.0))
        else:
            estimated_days = max(2.0, min(14.0, request.distance_km / 200.0))
        
        return ShippingEstimate(
            base_cost=round(base_cost, 2),
            distance_cost=round(distance_cost, 2),
            weight_cost=round(weight_cost, 2),
            total_cost=round(total_cost, 2),
            confidence=historical['confidence'] * 0.95,  # Slightly reduce confidence for adjustments
            estimated_days=round(estimated_days, 1),
            method=request.method,
            notes="Based on historical shipping data with adjustments"
        )
    
    def estimate_labor(self, request: LaborEstimateRequest) -> LaborEstimate:
        """Estimate labor costs with enhanced model"""
        try:
            # Get base rate from pricing resolver
            rate_data = pricing_resolver.get_labor_rate(request.role.value.title())
            if not rate_data:
                # Fallback rates if not in database
                fallback_rates = {
                    LaborRole.CARPENTER: 120.0,
                    LaborRole.PAINTER: 100.0,
                    LaborRole.ELECTRICIAN: 150.0,
                    LaborRole.PLUMBER: 140.0,
                    LaborRole.LABORER: 80.0,
                    LaborRole.PROJECT_MANAGER: 200.0,
                    LaborRole.DESIGNER: 150.0,
                    LaborRole.INSTALLER: 110.0
                }
                base_rate = fallback_rates.get(request.role, 100.0)
                efficiency = self.labor_efficiency.get(request.role, 1.0)
            else:
                base_rate = rate_data['hourly_rate']
                efficiency = rate_data.get('efficiency', self.labor_efficiency.get(request.role, 1.0))
            
            # Apply efficiency factor
            effective_hours = request.hours_required / efficiency
            
            # Calculate costs
            regular_hours = min(effective_hours, 8.0)  # 8-hour standard day
            regular_cost = regular_hours * base_rate
            
            overtime_hours = max(0, effective_hours - 8.0)
            overtime_rate = base_rate * 1.5  # 1.5x for overtime
            overtime_cost = overtime_hours * overtime_rate
            
            # Apply complexity multiplier
            complexity_multiplier = request.complexity
            regular_cost *= complexity_multiplier
            overtime_cost *= complexity_multiplier
            
            # Tool surcharge
            tool_surcharge = base_rate * 0.1 * effective_hours if request.tools_required else 0.0
            
            total_cost = regular_cost + overtime_cost + tool_surcharge
            
            # Estimate work duration
            estimated_days = effective_hours / 8.0  # 8 hours per day
            
            confidence = 0.85 if rate_data else 0.7
            
            return LaborEstimate(
                role=request.role,
                base_rate=round(base_rate, 2),
                regular_hours=round(regular_hours, 2),
                regular_cost=round(regular_cost, 2),
                overtime_hours=round(overtime_hours, 2),
                overtime_rate=round(overtime_rate, 2),
                overtime_cost=round(overtime_cost, 2),
                complexity_multiplier=complexity_multiplier,
                tool_surcharge=round(tool_surcharge, 2),
                total_cost=round(total_cost, 2),
                confidence=confidence,
                estimated_days=round(estimated_days, 1),
                notes=f"Based on {rate_data['vendor_name'] if rate_data else 'default'} rates" if rate_data else "Based on default rates"
            )
            
        except Exception as e:
            logger.error(f"Labor estimation error: {e}")
            # Fallback estimate
            return LaborEstimate(
                role=request.role,
                base_rate=100.0,
                regular_hours=request.hours_required,
                regular_cost=request.hours_required * 100.0,
                overtime_hours=0.0,
                overtime_rate=150.0,  # 1.5x base rate
                overtime_cost=0.0,
                complexity_multiplier=1.0,
                tool_surcharge=0.0,
                total_cost=request.hours_required * 100.0,
                confidence=0.5,
                estimated_days=request.hours_required / 8.0,
                notes="Fallback estimate due to error"
            )
    
    def estimate_project(self, request: ProjectEstimateRequest) -> ProjectEstimate:
        """Estimate complete project costs"""
        materials_estimates = []
        labor_estimates = []
        
        total_materials_cost = 0.0
        total_labor_cost = 0.0
        total_shipping_cost = 0.0
        
        confidence_scores = []
        
        # Estimate materials
        for material_req in request.materials:
            try:
                price_data = pricing_resolver.get_material_price(material_req.material_name)
                if price_data:
                    quantity_with_waste = material_req.quantity * (1 + material_req.waste_factor)
                    material_cost = quantity_with_waste * price_data['price']
                    total_materials_cost += material_cost
                    
                    materials_estimates.append({
                        'material_name': material_req.material_name,
                        'quantity': material_req.quantity,
                        'quantity_with_waste': round(quantity_with_waste, 3),
                        'unit': material_req.unit,
                        'unit_price': price_data['price'],
                        'total_cost': round(material_cost, 2),
                        'vendor': price_data['vendor_name'],
                        'confidence': price_data['confidence'],
                        'waste_factor': material_req.waste_factor
                    })
                    confidence_scores.append(price_data['confidence'])
                else:
                    # Fallback for unknown materials
                    fallback_cost = material_req.quantity * 100.0  # Arbitrary fallback
                    total_materials_cost += fallback_cost
                    materials_estimates.append({
                        'material_name': material_req.material_name,
                        'quantity': material_req.quantity,
                        'unit_price': 100.0,
                        'total_cost': round(fallback_cost, 2),
                        'vendor': 'Unknown',
                        'confidence': 0.3,
                        'waste_factor': material_req.waste_factor,
                        'notes': 'Estimated using fallback pricing'
                    })
                    confidence_scores.append(0.3)
            except Exception as e:
                logger.warning(f"Error estimating material {material_req.material_name}: {e}")
        
        # Estimate labor
        for labor_req in request.labor:
            try:
                labor_estimate = self.estimate_labor(labor_req)
                labor_estimates.append(labor_estimate)
                total_labor_cost += labor_estimate.total_cost
                confidence_scores.append(labor_estimate.confidence)
            except Exception as e:
                logger.warning(f"Error estimating labor for {labor_req.role}: {e}")
        
        # Estimate shipping if provided
        shipping_estimate = None
        if request.shipping:
            try:
                shipping_estimate = self.estimate_shipping(request.shipping)
                total_shipping_cost = shipping_estimate.total_cost
                confidence_scores.append(shipping_estimate.confidence)
            except Exception as e:
                logger.warning(f"Error estimating shipping: {e}")
        
        # Calculate totals
        subtotal = total_materials_cost + total_labor_cost + total_shipping_cost
        margin_amount = subtotal * request.margin
        tax_amount = (subtotal + margin_amount) * request.tax_rate
        total_cost = subtotal + margin_amount + tax_amount
        
        # Calculate overall confidence (weighted average)
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Estimate timeline (max of labor days + shipping days)
        labor_days = max([est.estimated_days for est in labor_estimates], default=0.0)
        shipping_days = shipping_estimate.estimated_days if shipping_estimate else 0.0
        timeline_days = labor_days + shipping_days
        
        return ProjectEstimate(
            materials_cost=round(total_materials_cost, 2),
            labor_cost=round(total_labor_cost, 2),
            shipping_cost=round(total_shipping_cost, 2),
            subtotal=round(subtotal, 2),
            margin_amount=round(margin_amount, 2),
            tax_amount=round(tax_amount, 2),
            total_cost=round(total_cost, 2),
            confidence=round(overall_confidence, 2),
            materials=materials_estimates,
            labor=labor_estimates,
            shipping=shipping_estimate,
            estimated_timeline_days=round(timeline_days, 1)
        )
    
    def save_shipping_quote(self, quote: ShippingQuoteCreate) -> bool:
        """Save a shipping quote to the database"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO shipping_quotes 
                    (route_hash, distance_km, weight_kg, type, base_fee_nis, per_km_nis, per_kg_nis, 
                     source, confidence, fetched_at)
                    VALUES (MD5(%s), %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    f"{quote.distance_km}:{quote.weight_kg}:{quote.method}",
                    quote.distance_km,
                    quote.weight_kg,
                    quote.method.value,
                    quote.base_fee_nis,
                    quote.per_km_nis,
                    quote.per_kg_nis,
                    quote.source,
                    quote.confidence
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving shipping quote: {e}")
            return False
        finally:
            conn.close()
    
    def update_rate_card(self, role: str, update: RateCardUpdate) -> bool:
        """Update or create a rate card"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rate_cards (role, hourly_rate_nis, default_efficiency, overtime_rules_json)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (role) 
                    DO UPDATE SET 
                        hourly_rate_nis = EXCLUDED.hourly_rate_nis,
                        default_efficiency = EXCLUDED.default_efficiency,
                        overtime_rules_json = EXCLUDED.overtime_rules_json,
                        updated_at = NOW()
                """, (
                    role,
                    update.hourly_rate_nis,
                    update.default_efficiency,
                    update.overtime_rules
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating rate card: {e}")
            return False
        finally:
            conn.close()

# Global instance
estimation_service = EstimationService()