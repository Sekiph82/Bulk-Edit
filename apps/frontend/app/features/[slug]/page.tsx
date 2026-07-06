import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { FEATURE_PAGES, getFeaturePage } from "@/lib/featurePages";
import FeaturePageContent from "@/components/marketing/FeaturePageContent";

export function generateStaticParams() {
  return FEATURE_PAGES.map((f) => ({ slug: f.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const feature = getFeaturePage(params.slug);
  if (!feature) return {};

  const url = `https://bulkeditapp.com/features/${feature.slug}`;
  return {
    title: feature.metaTitle,
    description: feature.metaDescription,
    alternates: { canonical: url },
    openGraph: {
      title: feature.metaTitle,
      description: feature.metaDescription,
      url,
      siteName: "Bulk Edit App",
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: feature.metaTitle,
      description: feature.metaDescription,
    },
  };
}

export default function FeatureSlugPage({ params }: { params: { slug: string } }) {
  const feature = getFeaturePage(params.slug);
  if (!feature) notFound();

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://bulkeditapp.com/" },
      { "@type": "ListItem", position: 2, name: "Features", item: "https://bulkeditapp.com/features" },
      {
        "@type": "ListItem",
        position: 3,
        name: feature.h1,
        item: `https://bulkeditapp.com/features/${feature.slug}`,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <FeaturePageContent feature={feature} />
    </>
  );
}
