"""
Profit & Cost Calculator API.
Calculates listing profitability using configurable Etsy fee profiles.
Never writes to Etsy. Profit data is an estimate — actual Etsy fees vary by account/region.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.models.listing import Listing
from app.models.cost_profile import CostProfile
from app.models.listing_cost import ListingCost
from app.schemas.profit import (
    CostProfileCreate,
    CostProfileResponse,
    CostProfileUpdate,
    ListingCostUpdate,
    ProfitCalculation,
    ProfitListingPage,
    ProfitListingRow,
    ProfitStatus,
    ProfitSummary,
)
from app.services.profit import calculate_profit, profit_status
import uuid

router = APIRouter(prefix="/profit", tags=["profit"])

ZERO = Decimal("0")
CENT = Decimal("0.01")


def _to_dec(val) -> Decimal:
    if val is None:
        return ZERO
    return Decimal(str(val))


def _listing_price(listing: Listing) -> Decimal:
    if listing.price_amount is not None and listing.price_divisor:
        return Decimal(str(listing.price_amount)) / Decimal(str(listing.price_divisor))
    return ZERO


async def _get_default_profile(org_id: str, db: AsyncSession) -> Optional[CostProfile]:
    res = await db.execute(
        select(CostProfile)
        .where(CostProfile.organization_id == org_id, CostProfile.is_default == True)  # noqa: E712
        .limit(1)
    )
    prof = res.scalar_one_or_none()
    if not prof:
        res = await db.execute(
            select(CostProfile).where(CostProfile.organization_id == org_id).limit(1)
        )
        prof = res.scalar_one_or_none()
    return prof


def _build_calc(
    listing: Listing,
    cost: Optional[ListingCost],
    profile: Optional[CostProfile],
) -> dict:
    sale_price = _listing_price(listing)
    txn_fee = _to_dec(profile.transaction_fee_percent) if profile else Decimal("0.065")
    pmt_fee = _to_dec(profile.payment_fee_percent) if profile else Decimal("0.030")
    pmt_fixed = _to_dec(profile.payment_fixed_fee) if profile else Decimal("0.25")
    lst_fee = _to_dec(profile.listing_fee) if profile else Decimal("0.20")
    offsite = _to_dec(profile.offsite_ads_percent) if profile else Decimal("0.15")
    target_margin = _to_dec(profile.target_margin_percent) if profile else Decimal("0.30")

    product_cost = _to_dec(cost.product_cost) if cost else ZERO
    shipping_cost = _to_dec(cost.shipping_cost) if cost else ZERO
    packaging_cost = _to_dec(cost.packaging_cost) if cost else ZERO
    ad_cost = _to_dec(cost.ad_cost) if cost else ZERO
    other_cost = _to_dec(cost.other_cost) if cost else ZERO
    include_offsite = cost.include_offsite_ads if cost else False

    return calculate_profit(
        sale_price=sale_price,
        product_cost=product_cost,
        shipping_cost=shipping_cost,
        packaging_cost=packaging_cost,
        ad_cost=ad_cost,
        other_cost=other_cost,
        include_offsite_ads=include_offsite,
        transaction_fee_percent=txn_fee,
        payment_fee_percent=pmt_fee,
        payment_fixed_fee=pmt_fixed,
        listing_fee=lst_fee,
        offsite_ads_percent=offsite,
        target_margin_percent=target_margin,
    )


@router.get("/summary", response_model=ProfitSummary)
async def get_profit_summary(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    listings_res = await db.execute(select(Listing).where(Listing.organization_id == org_id))
    listings = list(listings_res.scalars().all())
    listing_ids = [l.id for l in listings]

    costs_res = await db.execute(
        select(ListingCost).where(ListingCost.organization_id == org_id)
    )
    costs_map = {c.listing_id: c for c in costs_res.scalars().all()}
    profile = await _get_default_profile(org_id, db)

    with_costs = 0
    missing_costs = 0
    margins = []
    low_margin = 0
    loss = 0
    total_profit = ZERO
    currency = "USD"

    if profile:
        currency = profile.currency or "USD"
    elif listings and listings[0].currency_code:
        currency = listings[0].currency_code

    target_margin = _to_dec(profile.target_margin_percent) if profile else Decimal("0.30")

    for listing in listings:
        cost = costs_map.get(listing.id)
        if cost:
            with_costs += 1
        else:
            missing_costs += 1
            continue

        calc = _build_calc(listing, cost, profile)
        net = calc["net_profit"]
        margin = calc["margin_percent"]
        margins.append(margin)
        total_profit += net
        status = profit_status(net, margin, target_margin)
        if status == "loss":
            loss += 1
        elif status == "low_margin":
            low_margin += 1

    avg_margin = (sum(margins) / len(margins)).quantize(CENT) if margins else None

    return ProfitSummary(
        listings_with_costs=with_costs,
        listings_missing_costs=missing_costs,
        average_margin=avg_margin,
        low_margin_count=low_margin,
        loss_making_count=loss,
        estimated_total_profit=total_profit.quantize(CENT) if with_costs > 0 else None,
        currency=currency,
    )


@router.get("/listings", response_model=ProfitListingPage)
async def list_profit_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    loss_only: bool = Query(False),
    missing_costs: bool = Query(False),
    search: Optional[str] = Query(None),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    q = select(Listing).where(Listing.organization_id == org_id)
    if search:
        q = q.where(Listing.title.ilike(f"%{search}%"))

    listings_res = await db.execute(q)
    listings = list(listings_res.scalars().all())

    costs_res = await db.execute(
        select(ListingCost).where(ListingCost.organization_id == org_id)
    )
    costs_map = {c.listing_id: c for c in costs_res.scalars().all()}
    profile = await _get_default_profile(org_id, db)
    target_margin = _to_dec(profile.target_margin_percent) if profile else Decimal("0.30")

    rows: list[ProfitListingRow] = []
    for listing in listings:
        cost = costs_map.get(listing.id)

        if missing_costs and cost:
            continue
        if not cost:
            row = ProfitListingRow(
                listing_id=listing.id,
                title=listing.title,
                price=_listing_price(listing) if listing.price_amount else None,
                currency=listing.currency_code,
                status=ProfitStatus.MISSING_COSTS,
            )
            if missing_costs or not loss_only:
                rows.append(row)
            continue

        calc = _build_calc(listing, cost, profile)
        net = calc["net_profit"]
        margin = calc["margin_percent"]
        status_str = profit_status(net, margin, target_margin)

        if loss_only and status_str != "loss":
            continue

        rows.append(ProfitListingRow(
            listing_id=listing.id,
            title=listing.title,
            price=_listing_price(listing),
            currency=listing.currency_code,
            product_cost=calc["product_cost"],
            shipping_cost=calc["shipping_cost"],
            total_etsy_fees=calc["total_etsy_fees"],
            net_profit=net,
            margin_percent=margin,
            break_even_price=calc["break_even_price"],
            recommended_min_price=calc["recommended_min_price"],
            status=ProfitStatus(status_str),
        ))

    total = len(rows)
    offset = (page - 1) * page_size
    return ProfitListingPage(items=rows[offset: offset + page_size], total=total, page=page, page_size=page_size)


@router.get("/listings/{listing_id}", response_model=ProfitCalculation)
async def get_listing_profit(
    listing_id: str,
    shipping_charged: Decimal = Query(Decimal("0")),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    res = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    listing = res.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")

    cost_res = await db.execute(
        select(ListingCost).where(
            ListingCost.listing_id == listing_id,
            ListingCost.organization_id == org_id,
        )
    )
    cost = cost_res.scalar_one_or_none()
    profile = await _get_default_profile(org_id, db)
    target_margin = _to_dec(profile.target_margin_percent) if profile else Decimal("0.30")

    if not cost:
        # Return zero-cost calculation so UI can show default fees
        calc = calculate_profit(
            sale_price=_listing_price(listing),
            shipping_charged=max(ZERO, shipping_charged),
            transaction_fee_percent=_to_dec(profile.transaction_fee_percent) if profile else Decimal("0.065"),
            payment_fee_percent=_to_dec(profile.payment_fee_percent) if profile else Decimal("0.030"),
            payment_fixed_fee=_to_dec(profile.payment_fixed_fee) if profile else Decimal("0.25"),
            listing_fee=_to_dec(profile.listing_fee) if profile else Decimal("0.20"),
            target_margin_percent=target_margin,
        )
        net = calc["net_profit"]
        margin = calc["margin_percent"]
        status_val = ProfitStatus.MISSING_COSTS
    else:
        calc_with_sc = _build_calc(listing, cost, profile)
        if shipping_charged != ZERO:
            calc_with_sc = calculate_profit(
                sale_price=_listing_price(listing),
                shipping_charged=max(ZERO, shipping_charged),
                product_cost=_to_dec(cost.product_cost),
                shipping_cost=_to_dec(cost.shipping_cost),
                packaging_cost=_to_dec(cost.packaging_cost),
                ad_cost=_to_dec(cost.ad_cost),
                other_cost=_to_dec(cost.other_cost),
                include_offsite_ads=cost.include_offsite_ads,
                transaction_fee_percent=_to_dec(profile.transaction_fee_percent) if profile else Decimal("0.065"),
                payment_fee_percent=_to_dec(profile.payment_fee_percent) if profile else Decimal("0.030"),
                payment_fixed_fee=_to_dec(profile.payment_fixed_fee) if profile else Decimal("0.25"),
                listing_fee=_to_dec(profile.listing_fee) if profile else Decimal("0.20"),
                offsite_ads_percent=_to_dec(profile.offsite_ads_percent) if profile else Decimal("0.15"),
                target_margin_percent=target_margin,
            )
        calc = calc_with_sc
        net = calc["net_profit"]
        margin = calc["margin_percent"]
        status_val = ProfitStatus(profit_status(net, margin, target_margin))

    sale_price = _listing_price(listing)
    return ProfitCalculation(
        listing_id=listing_id,
        title=listing.title,
        price=sale_price,
        currency=listing.currency_code,
        sale_price=calc["sale_price"],
        shipping_charged=calc["shipping_charged"],
        gross_revenue=calc["gross_revenue"],
        product_cost=calc["product_cost"],
        shipping_cost=calc["shipping_cost"],
        packaging_cost=calc["packaging_cost"],
        ad_cost=calc["ad_cost"],
        other_cost=calc["other_cost"],
        etsy_transaction_fee=calc["etsy_transaction_fee"],
        etsy_payment_fee=calc["etsy_payment_fee"],
        etsy_listing_fee=calc["etsy_listing_fee"],
        etsy_offsite_ads_fee=calc["etsy_offsite_ads_fee"],
        total_etsy_fees=calc["total_etsy_fees"],
        total_costs=calc["total_costs"],
        net_profit=calc["net_profit"],
        margin_percent=calc["margin_percent"],
        break_even_price=calc["break_even_price"],
        recommended_min_price=calc["recommended_min_price"],
        roi_percent=calc["roi_percent"],
        status=status_val,
    )


@router.put("/listings/{listing_id}/costs")
async def upsert_listing_costs(
    listing_id: str,
    body: ListingCostUpdate,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    res = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found.")

    if body.cost_profile_id:
        prof_res = await db.execute(
            select(CostProfile).where(
                CostProfile.id == body.cost_profile_id,
                CostProfile.organization_id == org_id,
            )
        )
        if not prof_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Cost profile not found.")

    cost_res = await db.execute(
        select(ListingCost).where(
            ListingCost.listing_id == listing_id,
            ListingCost.organization_id == org_id,
        )
    )
    cost = cost_res.scalar_one_or_none()

    if cost:
        cost.product_cost = body.product_cost
        cost.shipping_cost = body.shipping_cost
        cost.packaging_cost = body.packaging_cost
        cost.ad_cost = body.ad_cost
        cost.other_cost = body.other_cost
        cost.include_offsite_ads = body.include_offsite_ads
        cost.cost_profile_id = body.cost_profile_id
        cost.notes = body.notes
    else:
        cost = ListingCost(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            listing_id=listing_id,
            product_cost=body.product_cost,
            shipping_cost=body.shipping_cost,
            packaging_cost=body.packaging_cost,
            ad_cost=body.ad_cost,
            other_cost=body.other_cost,
            include_offsite_ads=body.include_offsite_ads,
            cost_profile_id=body.cost_profile_id,
            notes=body.notes,
        )
        db.add(cost)

    await db.commit()
    return {"message": "Listing costs saved.", "listing_id": listing_id}


@router.get("/cost-profiles", response_model=list[CostProfileResponse])
async def list_cost_profiles(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    res = await db.execute(select(CostProfile).where(CostProfile.organization_id == org_id))
    return [CostProfileResponse.model_validate(p) for p in res.scalars().all()]


@router.post("/cost-profiles", response_model=CostProfileResponse, status_code=201)
async def create_cost_profile(
    body: CostProfileCreate,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    if body.is_default:
        # unset existing defaults
        existing = await db.execute(
            select(CostProfile).where(CostProfile.organization_id == org_id, CostProfile.is_default == True)  # noqa: E712
        )
        for p in existing.scalars().all():
            p.is_default = False

    profile = CostProfile(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        name=body.name,
        currency=body.currency,
        transaction_fee_percent=body.transaction_fee_percent,
        payment_fee_percent=body.payment_fee_percent,
        payment_fixed_fee=body.payment_fixed_fee,
        listing_fee=body.listing_fee,
        offsite_ads_percent=body.offsite_ads_percent,
        currency_conversion_percent=body.currency_conversion_percent,
        default_shipping_cost=body.default_shipping_cost,
        default_packaging_cost=body.default_packaging_cost,
        target_margin_percent=body.target_margin_percent,
        is_default=body.is_default,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return CostProfileResponse.model_validate(profile)


@router.put("/cost-profiles/{profile_id}", response_model=CostProfileResponse)
async def update_cost_profile(
    profile_id: str,
    body: CostProfileUpdate,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    res = await db.execute(
        select(CostProfile).where(CostProfile.id == profile_id, CostProfile.organization_id == org_id)
    )
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Cost profile not found.")

    if body.is_default and not profile.is_default:
        existing = await db.execute(
            select(CostProfile).where(CostProfile.organization_id == org_id, CostProfile.is_default == True)  # noqa: E712
        )
        for p in existing.scalars().all():
            p.is_default = False

    profile.name = body.name
    profile.currency = body.currency
    profile.transaction_fee_percent = body.transaction_fee_percent
    profile.payment_fee_percent = body.payment_fee_percent
    profile.payment_fixed_fee = body.payment_fixed_fee
    profile.listing_fee = body.listing_fee
    profile.offsite_ads_percent = body.offsite_ads_percent
    profile.currency_conversion_percent = body.currency_conversion_percent
    profile.default_shipping_cost = body.default_shipping_cost
    profile.default_packaging_cost = body.default_packaging_cost
    profile.target_margin_percent = body.target_margin_percent
    profile.is_default = body.is_default

    await db.commit()
    await db.refresh(profile)
    return CostProfileResponse.model_validate(profile)
