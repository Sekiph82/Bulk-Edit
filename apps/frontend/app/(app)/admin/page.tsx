"use client";

import { useEffect, useState } from "react";
import { useRouter, notFound } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

// /admin is no longer the owner entrypoint — the real owner console lives at
// /owner (served publicly at owner.bulkeditapp.com). This route only exists
// as a compatibility redirect for old links/bookmarks:
//   - unauthenticated or non-superuser -> real 404 (next/navigation notFound())
//   - confirmed superuser              -> same-origin redirect to /owner
// This page must never render any admin data itself.
export default function AdminCompatRedirectPage() {
  const router = useRouter();
  const [state, setState] = useState<"checking" | "denied">("checking");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setState("denied");
      return;
    }
    fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.user?.is_superuser === true) {
          router.replace("/owner");
        } else {
          setState("denied");
        }
      })
      .catch(() => setState("denied"));
  }, [router]);

  if (state === "denied") {
    notFound();
  }

  return null;
}
