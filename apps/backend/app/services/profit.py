"""
Profit & Cost Calculator engine.
Uses Decimal throughout for monetary accuracy.
No Etsy writes. No auto-apply. Estimate only.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0")
CENT = Decimal("0.01")
PCT2 = Decimal("0.01")


def calculate_profit(
    sale_price: Decimal,
    shipping_charged: Decimal = ZERO,
    product_cost: Decimal = ZERO,
    shipping_cost: Decimal = ZERO,
    packaging_cost: Decimal = ZERO,
    ad_cost: Decimal = ZERO,
    other_cost: Decimal = ZERO,
    include_offsite_ads: bool = False,
    transaction_fee_percent: Decimal = Decimal("0.065"),
    payment_fee_percent: Decimal = Decimal("0.030"),
    payment_fixed_fee: Decimal = Decimal("0.25"),
    listing_fee: Decimal = Decimal("0.20"),
    offsite_ads_percent: Decimal = Decimal("0.15"),
    target_margin_percent: Decimal = Decimal("0.30"),
) -> dict:
    sale_price = max(ZERO, sale_price)
    shipping_charged = max(ZERO, shipping_charged)
    gross_revenue = sale_price + shipping_charged

    etsy_txn_fee = (gross_revenue * transaction_fee_percent).quantize(CENT, ROUND_HALF_UP)
    etsy_pmt_fee = (gross_revenue * payment_fee_percent + payment_fixed_fee).quantize(CENT, ROUND_HALF_UP)
    etsy_listing_fee = listing_fee.quantize(CENT, ROUND_HALF_UP)
    etsy_offsite_fee = ZERO
    if include_offsite_ads:
        etsy_offsite_fee = (gross_revenue * offsite_ads_percent).quantize(CENT, ROUND_HALF_UP)

    total_etsy_fees = etsy_txn_fee + etsy_pmt_fee + etsy_listing_fee + etsy_offsite_fee
    total_direct = (
        max(ZERO, product_cost)
        + max(ZERO, shipping_cost)
        + max(ZERO, packaging_cost)
        + max(ZERO, ad_cost)
        + max(ZERO, other_cost)
    )
    total_costs = total_etsy_fees + total_direct
    net_profit = gross_revenue - total_costs

    if gross_revenue > ZERO:
        margin_pct = ((net_profit / gross_revenue) * 100).quantize(PCT2, ROUND_HALF_UP)
    else:
        margin_pct = ZERO

    # Break-even price: solve gross_revenue*(1 - var_fee) = fixed_fees + direct_costs
    var_fee_rate = transaction_fee_percent + payment_fee_percent
    if include_offsite_ads:
        var_fee_rate += offsite_ads_percent
    remaining = Decimal("1") - var_fee_rate

    if remaining > ZERO:
        fixed_side = payment_fixed_fee + listing_fee + total_direct
        break_even_gross = fixed_side / remaining
        break_even_price = max(ZERO, break_even_gross - shipping_charged).quantize(CENT, ROUND_HALF_UP)
    else:
        break_even_price = ZERO

    # Recommended min price: gross covers costs AND target margin
    if remaining > ZERO and (Decimal("1") - target_margin_percent) > ZERO:
        target_gross = (payment_fixed_fee + listing_fee + total_direct) / (remaining * (Decimal("1") - target_margin_percent))
        recommended_min = max(ZERO, target_gross - shipping_charged).quantize(CENT, ROUND_HALF_UP)
    else:
        recommended_min = break_even_price

    if total_direct > ZERO:
        roi_pct = ((net_profit / total_direct) * 100).quantize(PCT2, ROUND_HALF_UP)
    else:
        roi_pct = ZERO

    return {
        "gross_revenue": gross_revenue.quantize(CENT, ROUND_HALF_UP),
        "sale_price": sale_price.quantize(CENT, ROUND_HALF_UP),
        "shipping_charged": shipping_charged.quantize(CENT, ROUND_HALF_UP),
        "product_cost": max(ZERO, product_cost).quantize(CENT, ROUND_HALF_UP),
        "shipping_cost": max(ZERO, shipping_cost).quantize(CENT, ROUND_HALF_UP),
        "packaging_cost": max(ZERO, packaging_cost).quantize(CENT, ROUND_HALF_UP),
        "ad_cost": max(ZERO, ad_cost).quantize(CENT, ROUND_HALF_UP),
        "other_cost": max(ZERO, other_cost).quantize(CENT, ROUND_HALF_UP),
        "etsy_transaction_fee": etsy_txn_fee,
        "etsy_payment_fee": etsy_pmt_fee,
        "etsy_listing_fee": etsy_listing_fee,
        "etsy_offsite_ads_fee": etsy_offsite_fee,
        "total_etsy_fees": total_etsy_fees.quantize(CENT, ROUND_HALF_UP),
        "total_costs": total_costs.quantize(CENT, ROUND_HALF_UP),
        "net_profit": net_profit.quantize(CENT, ROUND_HALF_UP),
        "margin_percent": margin_pct,
        "break_even_price": break_even_price,
        "recommended_min_price": recommended_min,
        "roi_percent": roi_pct,
    }


def profit_status(net_profit: Decimal, margin_percent: Decimal, target_margin_percent: Decimal) -> str:
    if net_profit < ZERO:
        return "loss"
    if margin_percent < (target_margin_percent * 100).quantize(PCT2, ROUND_HALF_UP):
        return "low_margin"
    return "profitable"
