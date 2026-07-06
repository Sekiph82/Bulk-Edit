"use client";

import { useMemo, useState } from "react";

// Fully client-side. No backend call, no live Etsy fee lookup, nothing saved
// anywhere (no localStorage, no account). Default fee rates are editable
// assumptions, not claimed to be exact or official — see the disclaimer
// rendered alongside this component.

function NumberField({
  label,
  value,
  onChange,
  step = "0.01",
  suffix,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  step?: string;
  suffix?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <div className="relative">
        <input
          type="number"
          step={step}
          inputMode="decimal"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        {suffix && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">{suffix}</span>
        )}
      </div>
    </div>
  );
}

function toNumber(v: string): number {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
}

function money(n: number): string {
  return `$${n.toFixed(2)}`;
}

export default function EtsyFeeCalculator() {
  const [salePrice, setSalePrice] = useState("28.00");
  const [shippingCharged, setShippingCharged] = useState("4.50");
  const [itemCost, setItemCost] = useState("8.00");
  const [packagingCost, setPackagingCost] = useState("1.00");
  const [sellerShippingCost, setSellerShippingCost] = useState("4.00");
  const [discount, setDiscount] = useState("0.00");
  const [otherCosts, setOtherCosts] = useState("0.00");

  const [transactionFeePct, setTransactionFeePct] = useState("6.5");
  const [processingPct, setProcessingPct] = useState("3");
  const [processingFixed, setProcessingFixed] = useState("0.25");
  const [offsiteAdsPct, setOffsiteAdsPct] = useState("0");

  const results = useMemo(() => {
    const grossRevenue = Math.max(0, toNumber(salePrice) - toNumber(discount)) + toNumber(shippingCharged);
    const transactionFee = grossRevenue * (toNumber(transactionFeePct) / 100);
    const processingFee = grossRevenue * (toNumber(processingPct) / 100) + toNumber(processingFixed);
    const offsiteAdsFee = grossRevenue * (toNumber(offsiteAdsPct) / 100);
    const totalFees = transactionFee + processingFee + offsiteAdsFee;
    const totalCosts =
      toNumber(itemCost) + toNumber(packagingCost) + toNumber(sellerShippingCost) + toNumber(otherCosts) + totalFees;
    const netProfit = grossRevenue - totalCosts;
    const margin = grossRevenue > 0 ? (netProfit / grossRevenue) * 100 : 0;

    let note: string;
    if (grossRevenue <= 0) {
      note = "Enter a sale price to see an estimate.";
    } else if (netProfit < 0) {
      note = "At these inputs, this listing is estimated to run at a loss. Consider reviewing the price or costs before a bulk update.";
    } else if (margin < 20) {
      note = "Margin is thin at these inputs. Worth reviewing before applying a price rule across similar listings.";
    } else {
      note = "Margin looks healthy at these inputs — still worth spot-checking a few similar listings before a bulk update.";
    }

    return { grossRevenue, transactionFee, processingFee, offsiteAdsFee, totalFees, totalCosts, netProfit, margin, note };
  }, [
    salePrice, shippingCharged, itemCost, packagingCost, sellerShippingCost, discount, otherCosts,
    transactionFeePct, processingPct, processingFixed, offsiteAdsPct,
  ]);

  return (
    <div className="be-card p-6 sm:p-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Inputs */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Listing inputs</h2>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <NumberField label="Sale price" value={salePrice} onChange={setSalePrice} suffix="$" />
            <NumberField label="Shipping charged to buyer" value={shippingCharged} onChange={setShippingCharged} suffix="$" />
            <NumberField label="Item cost" value={itemCost} onChange={setItemCost} suffix="$" />
            <NumberField label="Packaging cost" value={packagingCost} onChange={setPackagingCost} suffix="$" />
            <NumberField label="Shipping cost you pay" value={sellerShippingCost} onChange={setSellerShippingCost} suffix="$" />
            <NumberField label="Discount amount" value={discount} onChange={setDiscount} suffix="$" />
            <NumberField label="Other costs" value={otherCosts} onChange={setOtherCosts} suffix="$" />
          </div>

          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Fee assumptions (editable)</h2>
          <p className="text-xs text-gray-400 mb-4">
            Defaults are common approximations, not official Etsy figures — edit these to match your own account and region.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <NumberField label="Transaction fee" value={transactionFeePct} onChange={setTransactionFeePct} suffix="%" />
            <NumberField label="Payment processing" value={processingPct} onChange={setProcessingPct} suffix="%" />
            <NumberField label="Payment fixed fee" value={processingFixed} onChange={setProcessingFixed} suffix="$" />
            <NumberField label="Offsite Ads (optional)" value={offsiteAdsPct} onChange={setOffsiteAdsPct} suffix="%" />
          </div>
        </div>

        {/* Results */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Estimated results</h2>
          <div className="space-y-2 text-sm mb-4">
            <div className="flex justify-between"><span className="text-gray-500">Gross revenue</span><span className="font-medium text-gray-900">{money(results.grossRevenue)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Estimated transaction fee</span><span className="text-gray-700">{money(results.transactionFee)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Estimated payment processing fee</span><span className="text-gray-700">{money(results.processingFee)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Estimated Offsite Ads fee</span><span className="text-gray-700">{money(results.offsiteAdsFee)}</span></div>
            <div className="flex justify-between border-t border-gray-100 pt-2"><span className="text-gray-500">Total estimated fees</span><span className="font-medium text-gray-900">{money(results.totalFees)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Total costs (fees + item + shipping + packaging)</span><span className="font-medium text-gray-900">{money(results.totalCosts)}</span></div>
          </div>

          <div className={`be-card p-5 mb-4 ${results.netProfit < 0 ? "bg-red-50 border-red-200" : "bg-green-50 border-green-200"}`}>
            <div className="flex justify-between items-baseline mb-1">
              <span className="text-sm font-semibold text-gray-700">Estimated net profit</span>
              <span className={`text-2xl font-bold ${results.netProfit < 0 ? "text-red-600" : "text-green-700"}`}>
                {money(results.netProfit)}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-xs text-gray-500">Estimated margin</span>
              <span className="text-sm font-medium text-gray-700">{results.margin.toFixed(1)}%</span>
            </div>
          </div>

          <p className="text-sm text-gray-600 leading-relaxed">{results.note}</p>
        </div>
      </div>

      <p className="mt-8 text-xs text-gray-500 leading-relaxed border-t border-gray-100 pt-5">
        This calculator is an estimate for planning purposes only. Etsy fees, taxes, ads, and payment
        processing charges can vary. Always verify current fees in your Etsy account and official Etsy
        documentation. No data entered here is saved or sent anywhere — everything runs in your browser.
      </p>
    </div>
  );
}
