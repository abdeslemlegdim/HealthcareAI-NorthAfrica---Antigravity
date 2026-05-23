
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "../styles/landing.css";

const LAYERS = ["ORIGIN", "DIAGNOSTICS", "ASSISTANT", "VITALS", "FUTURE"];
const LERP = 0.1;
const clamp = (val, min, max) => Math.min(Math.max(val, min), max);
const IS_TOUCH = typeof navigator !== 'undefined' && navigator.maxTouchPoints > 0;

const LandingPage = () => {
  const scrollTrackRef = useRef(null);
  const fillRef = useRef(null);
  const sceneRef = useRef(null);
  const labelRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const scrollElement = scrollTrackRef.current;
    if (!scrollElement) return;

    let currentY = 0;
    let targetY = 0;
    let raf = null;
    let lastTime = null;
    let touchRaf = null;
    let pendingY = null;
    let lastIndex = -1;

    const travel = () => Math.max(0, scrollElement.scrollHeight - window.innerHeight);

    const setY = (y) => {
      scrollElement.style.transform = `translate3d(0, ${y}px, 0)`;
    };

    const updateHeight = () => {
      const h = `${scrollElement.scrollHeight}px`;
      if (document.body.style.height !== h) document.body.style.height = h;
    };

    const updateUI = (progress) => {
      const p = clamp(progress, 0, 1);
      if (fillRef.current) fillRef.current.style.width = `${p * 100}%`;
      if (sceneRef.current) sceneRef.current.style.backgroundPositionY = `${(1 - p) * 100}%`;
      
      const index = Math.min(Math.floor(p * LAYERS.length), LAYERS.length - 1);
      if (index !== lastIndex) {
        lastIndex = index;
        if (labelRef.current) labelRef.current.textContent = LAYERS[index];
        setActiveIndex(index);
      }
    };

    const tick = (time) => {
      if (!lastTime) lastTime = time;
      const delta = (time - lastTime) / 16.666;
      lastTime = time;
      const lerpFactor = 1 - Math.pow(1 - LERP, delta);
      const diff = targetY - currentY;
      
      if (Math.abs(diff) > 0.01) {
        currentY += diff * lerpFactor;
        setY(currentY);
      } else if (currentY !== targetY) {
        currentY = targetY;
        setY(currentY);
      }
      raf = requestAnimationFrame(tick);
    };

    const onScroll = () => {
      const t = travel();
      const y = -t + window.scrollY;
      if (IS_TOUCH) {
        pendingY = y;
        if (!touchRaf) {
          touchRaf = requestAnimationFrame(() => {
            currentY = targetY = pendingY;
            setY(pendingY);
            touchRaf = null;
          });
        }
      } else {
        targetY = y;
      }
      const progress = t > 0 ? window.scrollY / t : 0;
      updateUI(clamp(progress, 0, 1));
    };

    const onResize = () => {
      updateHeight();
      const t = travel();
      if (IS_TOUCH) {
        currentY = targetY = -t + window.scrollY;
        setY(currentY);
      } else {
        targetY = -t + window.scrollY;
      }
      const progress = t > 0 ? window.scrollY / t : 0;
      updateUI(clamp(progress, 0, 1));
    };

    const resizeObserver = new ResizeObserver(onResize);
    resizeObserver.observe(scrollElement);

    updateHeight();
    const t = travel();
    const initialY = -t + clamp(window.scrollY, 0, t);
    currentY = targetY = initialY;
    setY(currentY);
    updateUI(t > 0 ? window.scrollY / t : 0);

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });

    if (!IS_TOUCH) {
      raf = requestAnimationFrame(tick);
    }

    // Scroll method for dots
    window.scrollToPanel = (index) => {
      const clamped = clamp(index, 0, LAYERS.length - 1);
      const progress = clamped / (LAYERS.length - 1);
      window.scrollTo({ top: travel() * progress, behavior: 'smooth' });
    };

    return () => {
      if (raf) cancelAnimationFrame(raf);
      if (touchRaf) cancelAnimationFrame(touchRaf);
      resizeObserver.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      document.body.style.height = '';
      delete window.scrollToPanel;
    };
  }, []);

  return (
    <div className="landing-page-root">
      <div id="hud">
        <span className="hud-title">HEALTHCARE<br/>OF THE<br/>FUTURE</span>
        <div className="progress-bar">
          <div id="progress_fill" className="progress-fill" ref={fillRef}></div>
        </div>
        <span id="hud_label" className="hud-label" ref={labelRef}>ORIGIN</span>
      </div>

      <nav id="panel_nav" aria-label="Panels">
        {LAYERS.map((layer, idx) => (
          <button 
            key={layer}
            className={`nav-dot ${activeIndex === idx ? 'is-active' : ''}`} 
            onClick={() => window.scrollToPanel && window.scrollToPanel(idx)}
            title={layer}
          />
        ))}
      </nav>

      <div className="scene" ref={sceneRef}>
        <div className="scroll-track" ref={scrollTrackRef}>

          <section className="panel" id="panel_earth">
            <div className="panel-inner">
              <span className="layer-bg" aria-hidden="true">ORIGIN</span>
              <div className="panel-copy">
                <p className="layer-tag">Layer I · Origin · ↓ Scroll down to explore</p>
                <h2>AI POWERED<br/>HEALTHCARE.</h2>
                <p className="layer-line">Trust the intelligence.<br/>The machine works for you.</p>
                <div className="scroll-hint" aria-label="Scroll to explore">
                  <span>↓</span>
                  <span className="scroll-hint-text">scroll down to explore</span>
                </div>
              </div>
            </div>
          </section>

          <section className="panel" id="panel_body">
            <div className="panel-inner is-right">
              <span className="layer-bg" aria-hidden="true">IMAGING</span>
              <div className="panel-copy align-right">
                <p className="layer-tag">Layer II · Diagnostics</p>
                <h2>SEE THE<br/>UNSEEN.</h2>
                <p className="layer-line mb-6">Medical imaging analysis powered by Grad-CAM.<br/>Detect anomalies in seconds.</p>
                <Link to="/imaging" className="inline-block border border-teal-500 text-teal-400 px-6 py-3 rounded-full uppercase tracking-widest text-xs hover:bg-teal-500 hover:text-white transition">
                  Open Diagnostics
                </Link>
              </div>
            </div>
          </section>

          <section className="panel" id="panel_mind">
            <div className="panel-inner is-center">
              <span className="layer-bg" aria-hidden="true">ASSISTANT</span>
              <div className="panel-copy align-center">
                <p className="layer-tag">Layer III · Intelligence</p>
                <h2>FULL<br/>CONFIDENCE.<br/>VERIFIED<br/>ANSWERS.</h2>
                <p className="layer-line mb-6">Our Hybrid RAG system relies on<br/>verified medical literature, not hallucinations.</p>
                <Link to="/chat" className="inline-block border border-teal-500 text-teal-400 px-6 py-3 rounded-full uppercase tracking-widest text-xs hover:bg-teal-500 hover:text-white transition">
                  Talk to AI Assistant
                </Link>
              </div>
            </div>
          </section>

          <section className="panel" id="panel_spirit">
            <div className="panel-inner is-right">
              <span className="layer-bg" aria-hidden="true">VITALS</span>
              <div className="panel-copy align-right">
                <p className="layer-tag">Layer IV · Measurement</p>
                <h2>REMOTE<br/>MONITORING.</h2>
                <p className="layer-line mb-6">Measure heart rate and vitals using<br/>just your device's camera.</p>
                <Link to="/vitals" className="inline-block border border-teal-500 text-teal-400 px-6 py-3 rounded-full uppercase tracking-widest text-xs hover:bg-teal-500 hover:text-white transition">
                  Measure Vitals
                </Link>
              </div>
            </div>
          </section>

          <section className="panel" id="panel_void">
            <div className="panel-inner is-center">
              <span className="layer-bg" aria-hidden="true">FUTURE</span>
              <div className="panel-copy align-center">
                <p className="layer-tag">Layer V · Terminal</p>
                <h2>EVERYTHING.<br/>AS PROMISED.</h2>
                <p className="layer-line mb-6">The future of healthcare is accessible,<br/>accurate, and immediate.</p>
                <Link to="/dashboard" className="inline-block bg-teal-500 text-white px-8 py-4 rounded-full uppercase tracking-widest text-xs hover:bg-teal-600 transition shadow-[0_0_20px_rgba(20,184,166,0.4)]">
                  Enter Dashboard
                </Link>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
};

export default LandingPage;
