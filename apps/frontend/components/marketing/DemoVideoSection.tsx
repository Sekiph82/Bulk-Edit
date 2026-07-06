"use client";

import { useState } from "react";
import Link from "next/link";
import FadeUp from "./FadeUp";

// Real path a future demo video would live at. If it doesn't exist yet, the
// <video> element's onError fires and we fall back to an honest "coming
// soon" placeholder instead of pretending a video plays. No autoplay, no
// sound — playback (if the file exists) only starts when the visitor clicks
// the native controls.
const DEMO_VIDEO_SRC = "/demo/bulk-edit-app-demo.mp4";
const DEMO_VIDEO_POSTER = "/demo/bulk-edit-app-demo-poster.png";

const STEPS = [
  { n: 1, label: "Select listings" },
  { n: 2, label: "Preview changes" },
  { n: 3, label: "Apply safely" },
  { n: 4, label: "Revert if needed" },
];

export default function DemoVideoSection() {
  const [videoAvailable, setVideoAvailable] = useState(true);

  return (
    <section className="py-20 px-6 sm:px-8 be-section-accent">
      <div className="max-w-4xl mx-auto text-center">
        <FadeUp>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            Watch the 60-second safety-first bulk editing flow
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto mb-10">
            From selecting listings to previewing changes and reverting safely, the demo walks
            through how Bulk Edit App helps avoid risky manual edits.
          </p>
        </FadeUp>

        <FadeUp delay={0.1}>
          {videoAvailable ? (
            <div className="rounded-2xl overflow-hidden border border-gray-200 shadow-lg bg-black">
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video
                className="w-full aspect-video"
                controls
                preload="metadata"
                poster={DEMO_VIDEO_POSTER}
                onError={() => setVideoAvailable(false)}
              >
                <source src={DEMO_VIDEO_SRC} type="video/mp4" />
              </video>
            </div>
          ) : (
            <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
              <div className="aspect-video flex flex-col items-center justify-center gap-4 bg-gradient-to-br from-indigo-50 to-purple-50 px-6">
                <div className="w-16 h-16 rounded-full bg-white shadow-md flex items-center justify-center">
                  <svg className="w-6 h-6 text-indigo-600 ml-0.5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-gray-700">Product tour coming soon</p>
                <p className="text-xs text-gray-400 max-w-sm">
                  Watch the 60-second tour soon — until then, here&apos;s what it walks through.
                </p>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 border-t border-gray-100">
                {STEPS.map((s) => (
                  <div key={s.n} className="py-4 px-2 text-center">
                    <div className="w-6 h-6 mx-auto mb-1.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center">
                      {s.n}
                    </div>
                    <p className="text-xs text-gray-600 font-medium">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </FadeUp>

        <FadeUp delay={0.18}>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-8">
            <Link href="/features" className="be-btn-secondary px-7 py-3">
              See all features
            </Link>
            <Link href="/register" className="be-btn-primary px-7 py-3">
              Try Bulk Edit App
            </Link>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
