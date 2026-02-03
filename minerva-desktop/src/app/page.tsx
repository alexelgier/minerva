"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { Toaster } from "@/components/ui/sonner";
import Image from "next/image";
import React from "react";

export default function DemoPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading (layout)...</div>}>
      <div className="minerva-container">
        {/* Minerva Header */}
        <header className="minerva-header">
          <div className="minerva-header-left">
            <Image
              src="/assets/MinervaLogo.png"
              alt="Minerva Logo"
              width={49}
              height={49}
              className="minerva-logo"
            />
          </div>
        </header>

        {/* Main Content */}
        <div className="minerva-content">
          <Toaster />
          <ThreadProvider>
            <StreamProvider>
              <ArtifactProvider>
                <Thread />
              </ArtifactProvider>
            </StreamProvider>
          </ThreadProvider>
        </div>
      </div>
    </React.Suspense>
  );
}
