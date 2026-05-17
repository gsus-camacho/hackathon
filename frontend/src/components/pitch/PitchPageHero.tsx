import React from "react";

interface Props {
  eyebrow: string;
  title: string;
  subtitle: string;
  testId?: string;
}

export const PitchPageHero: React.FC<Props> = ({ eyebrow, title, subtitle, testId = "pitch-page-hero" }) => (
  <section
    className="relative overflow-hidden rounded-2xl bg-bio-900 text-bio-100 p-6 mb-6 grain"
    data-testid={testId}
  >
    <span className="text-[10px] uppercase tracking-[0.25em] font-mono text-bio-500">{eyebrow}</span>
    <h2 className="font-heading text-2xl sm:text-3xl font-semibold text-white mt-2 max-w-2xl">{title}</h2>
    <p className="text-sm text-bio-200 mt-2 max-w-2xl">{subtitle}</p>
  </section>
);

export default PitchPageHero;
