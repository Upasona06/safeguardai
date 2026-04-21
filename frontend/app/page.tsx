"use client";
import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import AIDemo from "@/components/landing/AIDemo";
import Testimonials from "@/components/landing/Testimonials";
import CTASection from "@/components/landing/CTASection";
import Footer from "@/components/landing/Footer";
import Navbar from "@/components/Navbar";

export default function HomePage() {
  return (
    <main className="app-shell grid-bg overflow-x-hidden">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <AIDemo />
      <Testimonials />
      <CTASection />
      <Footer />
    </main>
  );
}
