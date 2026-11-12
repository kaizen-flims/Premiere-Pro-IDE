import React, { useEffect } from "react";
import { createRoot } from "react-dom/client";
import {
  LiquidGlassLogo,
  liquidGlassLogoFinishTime,
} from "./components/liquid-glass-logo";
import "./index.css";

declare global {
  interface Window {
    PodiumAirBoot?: {
      finish: () => void;
    };
  }
}

// Android's animator scale is forwarded by the native host. Make the same
// preference visible to ReactDrops' own renderer before it mounts.
const nativeReducedMotion =
  new URLSearchParams(window.location.search).get("reducedMotion") === "1";

if (nativeReducedMotion) {
  const browserMatchMedia = window.matchMedia.bind(window);
  window.matchMedia = ((query: string) => {
    if (query.includes("prefers-reduced-motion")) {
      return {
        matches: true,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      } as MediaQueryList;
    }
    return browserMatchMedia(query);
  }) as typeof window.matchMedia;
}

function BootAnimation() {
  useEffect(() => {
    let finished = false;
    let finishTimer: number | undefined;
    let watchdogTimer: number | undefined;
    let observer: MutationObserver | undefined;

    const reducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    const finishAfter = (seconds: number) => {
      if (finished) return;
      finished = true;
      if (watchdogTimer !== undefined) window.clearTimeout(watchdogTimer);
      finishTimer = window.setTimeout(
        () => window.PodiumAirBoot?.finish(),
        seconds * 1000,
      );
    };

    const logoRoot = document.querySelector<HTMLElement>(".liquid-glass-logo");
    if (!logoRoot) {
      finishAfter(0.1);
      return () => {};
    }

    const fallbackImage = logoRoot.querySelector<HTMLImageElement>(
      ".liquid-glass-logo-fallback img",
    );

    if (reducedMotion) {
      if (fallbackImage && !fallbackImage.complete) {
        fallbackImage.addEventListener("load", () => finishAfter(0.12), {
          once: true,
        });
      } else {
        requestAnimationFrame(() => finishAfter(0.12));
      }
    } else {
      const animationHold =
        liquidGlassLogoFinishTime({
          ending: "logo",
          background: "#000000",
        }) + 0.35;

      const finishWhenRendererReady = () => finishAfter(animationHold);

      if (logoRoot.hasAttribute("data-liquid-glass-ready")) {
        finishWhenRendererReady();
      } else {
        observer = new MutationObserver(() => {
          if (logoRoot.hasAttribute("data-liquid-glass-ready")) {
            observer?.disconnect();
            finishWhenRendererReady();
          }
        });
        observer.observe(logoRoot, {
          attributes: true,
          attributeFilter: ["data-liquid-glass-ready"],
        });

        // If WebGL 2 is unavailable, keep the component's own image fallback
        // on screen briefly instead of waiting for a canvas-ready signal.
        if (!("WebGL2RenderingContext" in window)) {
          if (fallbackImage && !fallbackImage.complete) {
            fallbackImage.addEventListener("load", () => finishAfter(0.85), {
              once: true,
            });
          } else {
            requestAnimationFrame(() => finishAfter(0.85));
          }
        }

        // If a device exposes WebGL 2 but its driver cannot initialize it,
        // dismiss cleanly while leaving ReactDrops' fallback visible.
        watchdogTimer = window.setTimeout(() => finishAfter(0.25), 3000);
      }
    }

    return () => {
      observer?.disconnect();
      if (finishTimer !== undefined) window.clearTimeout(finishTimer);
      if (watchdogTimer !== undefined) window.clearTimeout(watchdogTimer);
    };
  }, []);

  return (
    <main className="podium-boot-stage">
      <LiquidGlassLogo
        logo="./podium-air-logo.svg"
        ending="logo"
        theme="light"
        tileColor="#ffffff"
        background="#000000"
        depth={1.25}
        dispersion={2.8}
        relief={1.55}
        caustics={3}
        highlights={2.65}
        bloom={0.5}
        echoTint={0.81}
        innerWallFocus={1}
        finalLogoScale={1}
        style={{ height: 480, width: "100%" }}
      />
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<BootAnimation />);
