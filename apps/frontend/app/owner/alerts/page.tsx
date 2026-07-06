"use client";

import { useCallback, useEffect, useState } from "react";
import {
  adminListAlerts,
  adminUpdateAlert,
  adminTestAlert,
  adminRunAlertCheck,
  type AdminAlertRuleOut,
  ApiError,
} from "@/lib/api";
import { PageHeader, Card, fmt } from "@/components/owner/OwnerUI";

function RuleCard({ rule, onChanged }: { rule: AdminAlertRuleOut; onChanged: () => void }) {
  const [enabled, setEnabled] = useState(rule.enabled);
  const [threshold, setThreshold] = useState(String(rule.threshold_count));
  const [window, setWindowMin] = useState(String(rule.window_minutes));
  const [emailEnabled, setEmailEnabled] = useState(rule.channel_email_enabled);
  const [emailTo, setEmailTo] = useState(rule.channel_email_to ?? "");
  const [slackEnabled, setSlackEnabled] = useState(rule.channel_slack_enabled);
  const [slackWebhook, setSlackWebhook] = useState("");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  function flash(m: string) {
    setMsg(m);
    setTimeout(() => setMsg(null), 4000);
  }

  async function save() {
    setSaving(true);
    setErr(null);
    try {
      await adminUpdateAlert(rule.id, {
        enabled,
        threshold_count: Number(threshold),
        window_minutes: Number(window),
        channel_email_enabled: emailEnabled,
        channel_email_to: emailTo || null,
        channel_slack_enabled: slackEnabled,
        ...(slackWebhook ? { slack_webhook_url: slackWebhook } : {}),
      });
      setSlackWebhook("");
      flash("Saved.");
      onChanged();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function runTest() {
    setTesting(true);
    setErr(null);
    try {
      const result = await adminTestAlert(rule.id);
      flash(result.message);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Test failed.");
    } finally {
      setTesting(false);
    }
  }

  return (
    <Card>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">{rule.name}</h3>
          <p className="text-xs text-gray-400">event: {rule.event_type} · last triggered: {fmt(rule.last_triggered_at)}</p>
        </div>
        <label className="flex items-center gap-2 text-xs text-gray-600">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          Enabled
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Threshold count</label>
          <input
            type="number"
            min={1}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Window (minutes)</label>
          <input
            type="number"
            min={1}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            value={window}
            onChange={(e) => setWindowMin(e.target.value)}
          />
        </div>
      </div>

      <div className="border-t border-gray-100 pt-3 mb-3">
        <label className="flex items-center gap-2 text-xs text-gray-600 mb-1.5">
          <input type="checkbox" checked={emailEnabled} onChange={(e) => setEmailEnabled(e.target.checked)} />
          Email notification
        </label>
        {emailEnabled && (
          <input
            type="email"
            placeholder="alerts@yourcompany.com (defaults to support email)"
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            value={emailTo}
            onChange={(e) => setEmailTo(e.target.value)}
          />
        )}
      </div>

      <div className="border-t border-gray-100 pt-3 mb-4">
        <label className="flex items-center gap-2 text-xs text-gray-600 mb-1.5">
          <input type="checkbox" checked={slackEnabled} onChange={(e) => setSlackEnabled(e.target.checked)} />
          Slack notification
        </label>
        {slackEnabled && (
          <>
            <input
              type="password"
              placeholder={rule.slack_webhook_configured ? "Webhook configured — enter a new URL to replace it" : "https://hooks.slack.com/services/…"}
              className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={slackWebhook}
              onChange={(e) => setSlackWebhook(e.target.value)}
            />
            <p className="text-[11px] text-gray-400 mt-1">
              {rule.slack_webhook_configured ? "A webhook is already saved (never shown here)." : "No webhook saved yet."} Leave blank to keep it unchanged.
            </p>
          </>
        )}
      </div>

      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
      {msg && <p className="text-sm text-green-600 mb-2">{msg}</p>}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="text-xs font-medium text-white bg-indigo-600 rounded-lg px-3 py-1.5 hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={runTest}
          disabled={testing}
          className="text-xs font-medium text-indigo-600 border border-indigo-200 rounded-lg px-3 py-1.5 hover:bg-indigo-50 disabled:opacity-50"
        >
          {testing ? "Sending…" : "Send test alert"}
        </button>
      </div>
    </Card>
  );
}

export default function OwnerAlertsPage() {
  const [rules, setRules] = useState<AdminAlertRuleOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const [checkResult, setCheckResult] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    adminListAlerts()
      .then(setRules)
      .catch(() => setError("Failed to load alert rules."));
  }, []);

  useEffect(() => { load(); }, [load]);

  async function runCheckNow() {
    setChecking(true);
    setCheckResult(null);
    try {
      const result = await adminRunAlertCheck();
      setCheckResult(
        result.triggered.length > 0
          ? `Checked ${result.checked} rule(s). Triggered: ${result.triggered.join(", ")}.`
          : `Checked ${result.checked} rule(s). Nothing triggered.`
      );
      load();
    } catch {
      setCheckResult("Alert check failed to run.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <main className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-start justify-between mb-6">
        <PageHeader title="Alerts" sub="Notification rules for critical platform events — superuser only" />
        <button
          type="button"
          onClick={runCheckNow}
          disabled={checking}
          className="text-xs font-medium text-white bg-gray-800 rounded-lg px-3 py-2 hover:bg-gray-900 disabled:opacity-50 whitespace-nowrap"
        >
          {checking ? "Checking…" : "Run alert check now"}
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-xs text-blue-800 mb-6">
        There is no background scheduler in this codebase yet — alerts are evaluated on demand only, via this button.
      </div>

      {checkResult && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{checkResult}</div>}
      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">{error}</div>}
      {!rules && !error && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}

      <div className="space-y-4">
        {rules?.map((r) => <RuleCard key={r.id} rule={r} onChanged={load} />)}
      </div>
    </main>
  );
}
