"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

const CONTACT_CARDS = [
  {
    icon: "✉️",
    title: "Email Support",
    desc: "Send us a message and we'll get back to you within one business day.",
    action: "support@bulkeditapp.com",
    href: "mailto:support@bulkeditapp.com",
    cta: "Send email",
  },
  {
    icon: "💬",
    title: "FAQ",
    desc: "Browse common questions about safety, billing, AI tools, and Etsy connection.",
    action: "Visit help center",
    href: "/faq",
    cta: "Browse FAQ",
  },
  {
    icon: "🐛",
    title: "Report a Bug",
    desc: "Found something broken? Open a GitHub issue and we'll track it down.",
    action: "github.com/Sekiph82/Bulk Edit App",
    href: "https://github.com/Sekiph82/Bulk Edit App/issues",
    cta: "Open issue",
  },
  {
    icon: "🚀",
    title: "Feature Request",
    desc: "Have an idea? We'd love to hear it. Use the demo form below or open an issue.",
    action: "Share an idea",
    href: "#demo-form",
    cta: "Share idea",
  },
];

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type FormState = "idle" | "sending" | "sent" | "error";

function FadeUp({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.45, delay, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function ContactContent() {
  const reduced = useReducedMotion();
  const [formState, setFormState] = useState<FormState>("idle");
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [resultMessage, setResultMessage] = useState("");
  const [delivered, setDelivered] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormState("sending");
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setResultMessage(
          Array.isArray(data.detail)
            ? data.detail.map((d: { msg: string }) => d.msg).join(" ")
            : data.detail || "Something went wrong. Please try again or email us directly."
        );
        setFormState("error");
        return;
      }
      setDelivered(Boolean(data.delivered));
      setResultMessage(data.message || "Thanks for reaching out!");
      setFormState("sent");
    } catch {
      setResultMessage("Network error. Please try again or email us directly.");
      setFormState("error");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Hero */}
      <section className="be-hero-bg pt-16 pb-16 px-6 sm:px-8 text-center">
        <div className="max-w-2xl mx-auto">
          <FadeUp>
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Contact
            </span>
          </FadeUp>
          <FadeUp delay={0.07}>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight mb-4">
              We&apos;re here to help
            </h1>
          </FadeUp>
          <FadeUp delay={0.13}>
            <p className="text-lg text-gray-500">
              Questions about billing, Etsy connection, safety, or just want to say hello? Pick a channel below.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* Contact cards */}
      <section className="py-16 px-6 sm:px-8 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {CONTACT_CARDS.map((card, i) => (
              <FadeUp key={card.title} delay={i * 0.07}>
                <motion.a
                  href={card.href}
                  className="be-contact-card block h-full no-underline"
                  whileHover={reduced ? {} : { y: -4 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="text-3xl mb-2" role="img" aria-label={card.title}>
                    {card.icon}
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">{card.title}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed flex-1">{card.desc}</p>
                  <span className="inline-block mt-2 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors">
                    {card.cta} →
                  </span>
                </motion.a>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* Contact form */}
      <section id="demo-form" className="py-16 px-6 sm:px-8 be-section-accent">
        <div className="max-w-2xl mx-auto">
          <FadeUp className="text-center mb-10">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Send us a message</h2>
            <p className="text-gray-500 text-sm">
              Or write directly to{" "}
              <a href="mailto:support@bulkeditapp.com" className="text-indigo-600 hover:underline">
                support@bulkeditapp.com
              </a>
              .
            </p>
          </FadeUp>

          {formState === "sent" ? (
            <FadeUp>
              <div className={`bg-white border rounded-2xl p-10 text-center shadow-sm ${delivered ? "border-green-200" : "border-amber-200"}`}>
                <div className="text-4xl mb-4">{delivered ? "✅" : "ℹ️"}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {delivered ? "Thanks for reaching out!" : "Message not delivered"}
                </h3>
                <p className="text-gray-500 text-sm mb-6">{resultMessage}</p>
                <button
                  onClick={() => { setFormState("idle"); setForm({ name: "", email: "", subject: "", message: "" }); }}
                  className="be-btn-secondary px-6 py-2 text-sm"
                >
                  Send another message
                </button>
              </div>
            </FadeUp>
          ) : formState === "error" ? (
            <FadeUp>
              <div className="bg-white border border-red-200 rounded-2xl p-10 text-center shadow-sm">
                <div className="text-4xl mb-4">⚠️</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h3>
                <p className="text-gray-500 text-sm mb-6">{resultMessage}</p>
                <button
                  onClick={() => setFormState("idle")}
                  className="be-btn-secondary px-6 py-2 text-sm"
                >
                  Try again
                </button>
              </div>
            </FadeUp>
          ) : (
            <FadeUp>
              <form
                onSubmit={handleSubmit}
                className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm space-y-5"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label htmlFor="contact-name" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Name
                    </label>
                    <input
                      id="contact-name"
                      name="name"
                      type="text"
                      required
                      value={form.name}
                      onChange={handleChange}
                      placeholder="Your name"
                      className="w-full rounded-lg border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition"
                    />
                  </div>
                  <div>
                    <label htmlFor="contact-email" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Email
                    </label>
                    <input
                      id="contact-email"
                      name="email"
                      type="email"
                      required
                      value={form.email}
                      onChange={handleChange}
                      placeholder="you@example.com"
                      className="w-full rounded-lg border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="contact-subject" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Subject
                  </label>
                  <select
                    id="contact-subject"
                    name="subject"
                    required
                    value={form.subject}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition bg-white"
                  >
                    <option value="" disabled>Select a topic…</option>
                    <option value="billing">Billing & subscription</option>
                    <option value="etsy">Etsy connection</option>
                    <option value="safety">Safety & backups</option>
                    <option value="ai">AI tools</option>
                    <option value="bug">Bug report</option>
                    <option value="feature">Feature request</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="contact-message" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Message
                  </label>
                  <textarea
                    id="contact-message"
                    name="message"
                    required
                    rows={5}
                    value={form.message}
                    onChange={handleChange}
                    placeholder="Describe your question or issue…"
                    className="w-full rounded-lg border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition resize-none"
                  />
                </div>

                <div className="flex items-center justify-between pt-1">
                  <p className="text-xs text-gray-400">
                    We reply within 1 business day.
                  </p>
                  <button
                    type="submit"
                    disabled={formState === "sending"}
                    className="be-btn-primary px-7 py-2.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {formState === "sending" ? "Sending…" : "Send message"}
                  </button>
                </div>
              </form>
            </FadeUp>
          )}
        </div>
      </section>

      {/* FAQ cross-link */}
      <section className="py-12 px-6 sm:px-8 bg-white border-t border-gray-100">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-gray-500 text-sm mb-3">
            Looking for a quick answer?
          </p>
          <Link href="/faq" className="be-btn-secondary px-6 py-2.5 text-sm">
            Browse the FAQ →
          </Link>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}
