"use client";

import Navbar from "../components/landing/Navbar";
import HeroSection from "../components/landing/HeroSection";
import WhatIsSentinel from "../components/landing/WhatIsSentinel";
import WhyCompaniesNeedSentinel from "../components/landing/WhyCompaniesNeedSentinel";
import CoreCapabilities from "../components/landing/CoreCapabilities";
import RequestJourney from "../components/landing/RequestJourney";
import IntegrationsSection from "../components/landing/IntegrationsSection";
import EnterpriseResults from "../components/landing/EnterpriseResults";
import TestimonialsSection from "../components/landing/TestimonialsSection";
import PricingSection from "../components/landing/PricingSection";
import FaqSection from "../components/landing/FaqSection";
import FinalCtaSection from "../components/landing/FinalCtaSection";
import FooterSection from "../components/landing/FooterSection";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#07111F] text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
      {/* Fixed Header */}
      <Navbar />

      {/* 1. HERO SECTION: Dark Luxury Theme (#07111F / #0D1324) */}
      <HeroSection />

      {/* DUAL MOOD TRANSITION TO WARM LIGHT THEME (#FAFAF8 / #F8F7F2) */}
      <div className="bg-[#FAFAF8]">
        {/* 2. WHAT IS SENTINEL */}
        <WhatIsSentinel />

        {/* 3. WHY COMPANIES NEED SENTINEL (Problem vs. Solution) */}
        <WhyCompaniesNeedSentinel />

        {/* 4. CORE CAPABILITIES (5 Key Pillars with Custom Visual Illustrations) */}
        <CoreCapabilities />

        {/* 5. HOW ONE AI REQUEST TRAVELS (Interactive Request Journey) */}
        <RequestJourney />

        {/* 6. ENTERPRISE INTEGRATIONS */}
        <IntegrationsSection />

        {/* 7. ENTERPRISE RESULTS & METRICS */}
        <EnterpriseResults />

        {/* 8. TESTIMONIALS */}
        <TestimonialsSection />

        {/* 9. PRICING PREVIEW */}
        <PricingSection />

        {/* 10. FREQUENTLY ASKED QUESTIONS */}
        <FaqSection />
      </div>

      {/* DUAL MOOD TRANSITION BACK TO DARK LUXURY THEME FOR FINAL CTA & FOOTER */}
      {/* 11. FINAL CTA SECTION */}
      <FinalCtaSection />

      {/* 12. ENTERPRISE FOOTER */}
      <FooterSection />
    </main>
  );
}
