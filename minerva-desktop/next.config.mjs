/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;

// Note: For Tauri production builds (tauri:build), you need to:
// 1. Add `output: "export"` and `images: { unoptimized: true }` above
// 2. Remove or rename src/app/api/ (static export doesn't support API routes)
// 3. Set NEXT_PUBLIC_API_URL to your LangGraph server directly (not via passthrough)
// For development (tauri:dev), no changes needed - uses dev server.
