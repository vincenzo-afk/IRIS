# IRIS Showcase Video

This directory contains the editable HyperFrames composition used by the project README. The source is [`index.html`](index.html); the delivered silent MP4 is [`renders/iris-overview.mp4`](renders/iris-overview.mp4).

## Requirements

Node.js 22 or newer and FFmpeg are required by HyperFrames. Install the locked JavaScript dependencies with:

```bash
npm install
```

## Development loop

Run the static linter while editing, then the full browser gate with snapshots:

```bash
npm run lint
npm run check
```

The composition is a 1920×1080, 27-second, six-scene overview. Typography, colors, layout, timing, and copy are authored directly in `index.html` and the GSAP timeline is registered under the `iris-overview` composition ID.

## Render

Render the stable repository artifact with:

```bash
npm run render
```

The output is written to `renders/iris-overview.mp4`. Snapshot PNGs produced by HyperFrames are local review artifacts and are ignored by the repository’s root `.gitignore`.
