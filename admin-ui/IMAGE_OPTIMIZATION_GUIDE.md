# Image Optimization Guide - AISIN Logo

## Performance Metrics Identified

Based on performance diagnostics run on the admin UI:

| Metric | Value | Issue |
|--------|-------|-------|
| **LCP (Largest Contentful Paint)** | 17,650 ms | Extremely slow on 3G |
| **Render Delay** | 17,638 ms | Image blocking render |
| **Wasted Image Data** | 14.3 kB | Oversized asset |
| **Original Size** | 400×179 px | Served at full resolution |
| **Display Size** | 149×67 px (CSS: 72×30 px) | Only 37% of pixels used |

## Immediate Fixes Applied

### 1. Added Explicit Dimensions to `<img>` Tag
```jsx
<img 
  src="/AISIN_Logo.jpg" 
  alt="Aisin logo" 
  width="149" 
  height="67" 
  loading="eager" 
  fetchpriority="high"
/>
```

**Benefits:**
- Prevents layout shift (CLS improvement)
- Browser reserves space before image loads
- `fetchpriority="high"` tells browser to prioritize logo
- `loading="eager"` ensures immediate loading (it's above-the-fold)

### 2. CSS Already Optimized
The CSS correctly sizes the image for display:
```css
.brand img {
  width: 72px;
  height: 30px;
  object-fit: contain;
}
```

## Recommended Next Steps

### Option A: Create Right-Sized Images (Quick Win)

Create properly sized versions for different screen densities:

```bash
# Standard resolution (72×30 display, serve 149×67 source)
# Already have: AISIN_Logo.jpg (400×179) - 15.6 KB

# Create optimized version sized for actual display:
# Target: 149×67 pixels (matches declared width/height)
# Expected savings: ~8-10 KB
```

**Tools you can use:**
- **ImageMagick**: `magick convert AISIN_Logo.jpg -resize 149x67 AISIN_Logo-149x67.jpg`
- **Sharp (Node.js)**: See `optimize-images.js` script below
- **Online**: TinyJPG, Squoosh.app

### Option B: Convert to Modern Formats (Best Performance)

Use WebP or AVIF for superior compression:

```html
<picture>
  <source srcset="/aisin-logo.avif" type="image/avif">
  <source srcset="/aisin-logo.webp" type="image/webp">
  <img 
    src="/AISIN_Logo-149x67.jpg" 
    alt="Aisin logo"
    width="149"
    height="67"
    loading="eager"
    fetchpriority="high"
  />
</picture>
```

**Expected Savings:**
- WebP: 25-35% smaller than JPEG
- AVIF: 40-50% smaller than JPEG
- Total savings: ~6-8 KB

### Option C: Inline Critical Images (Advanced)

For very small logos, consider inlining as data URI or inline SVG (if you have vector source):

```jsx
// Base64 inline (only for images < 5 KB after optimization)
<img src="data:image/jpeg;base64,/9j/4AAQ..." alt="Aisin logo" />
```

**Trade-offs:**
- ✅ Zero network requests
- ✅ Instant render
- ❌ Increases HTML bundle size
- ❌ Not cacheable separately

## Implementation Priority

### 🔴 Priority 1: Right-size the image (Do this first)
1. Create 149×67 version of AISIN_Logo.jpg
2. Replace in `/admin-ui/public/`
3. Test in DevTools (should see ~8 KB saved)

### 🟡 Priority 2: Modern format conversion
1. Generate WebP version
2. Update JSX to use `<picture>` element
3. Verify browser support (WebP: 96%+ modern browsers)

### 🟢 Priority 3: Optimize for retina displays
1. Create 2x version (298×134) for high-DPI screens
2. Use `srcset` attribute
3. Let browser choose appropriate version

## Automation Script

Save this as `admin-ui/optimize-images.js`:

\`\`\`javascript
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function optimizeAisinLogo() {
  const input = path.join(__dirname, 'public', 'AISIN_Logo.jpg');
  const outputDir = path.join(__dirname, 'public');

  console.log('Optimizing AISIN_Logo.jpg...');

  // 1. Create right-sized JPEG (149×67)
  await sharp(input)
    .resize(149, 67, { fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 0 } })
    .jpeg({ quality: 85, progressive: true })
    .toFile(path.join(outputDir, 'AISIN_Logo-149x67.jpg'));

  // 2. Create WebP version
  await sharp(input)
    .resize(149, 67, { fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 0 } })
    .webp({ quality: 85 })
    .toFile(path.join(outputDir, 'aisin-logo.webp'));

  // 3. Create 2x retina version (298×134)
  await sharp(input)
    .resize(298, 134, { fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 0 } })
    .jpeg({ quality: 85, progressive: true })
    .toFile(path.join(outputDir, 'AISIN_Logo-298x134.jpg'));

  // 4. Create 2x WebP
  await sharp(input)
    .resize(298, 134, { fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 0 } })
    .webp({ quality: 85 })
    .toFile(path.join(outputDir, 'aisin-logo@2x.webp'));

  console.log('✅ Optimization complete!');
  
  // Show file sizes
  const files = [
    'AISIN_Logo.jpg',
    'AISIN_Logo-149x67.jpg',
    'aisin-logo.webp',
    'AISIN_Logo-298x134.jpg',
    'aisin-logo@2x.webp'
  ];

  console.log('\nFile sizes:');
  files.forEach(file => {
    const filepath = path.join(outputDir, file);
    if (fs.existsSync(filepath)) {
      const stats = fs.statSync(filepath);
      console.log(\`  \${file}: \${(stats.size / 1024).toFixed(2)} KB\`);
    }
  });
}

optimizeAisinLogo().catch(console.error);
\`\`\`

**To run:**
```bash
cd admin-ui
npm install sharp
node optimize-images.js
```

## Final Implementation with Modern Formats

Once optimized images are generated, update `main.jsx`:

```jsx
<div className="brand">
  <picture>
    <source 
      srcSet="/aisin-logo.webp 1x, /aisin-logo@2x.webp 2x" 
      type="image/webp" 
    />
    <img 
      src="/AISIN_Logo-149x67.jpg"
      srcSet="/AISIN_Logo-149x67.jpg 1x, /AISIN_Logo-298x134.jpg 2x"
      alt="Aisin logo"
      width="149"
      height="67"
      loading="eager"
      fetchpriority="high"
    />
  </picture>
  <div>
    <strong>Employee Assistant</strong>
    <small>Server administration</small>
  </div>
</div>
```

## Testing

After implementing changes:

1. **Lighthouse**: Run audit in DevTools → Lighthouse
2. **Network tab**: Verify smaller file size downloaded
3. **Coverage**: Check unused CSS/JS isn't blocking
4. **WebPageTest**: Test on simulated 3G network

**Expected improvements:**
- LCP: < 2,500 ms (down from 17,650 ms)
- Wasted bytes: ~0 KB (down from 14.3 KB)
- Overall load time: 10-15 seconds faster on 3G

## Browser Support

| Format | Support | Fallback Strategy |
|--------|---------|-------------------|
| WebP | 96%+ | JPEG fallback via `<picture>` |
| AVIF | 85%+ | WebP → JPEG cascade |
| Responsive images (srcset) | 98%+ | Falls back to `src` |

## Additional Resources

- [WebP conversion guide](https://web.dev/serve-images-webp/)
- [Responsive images guide](https://web.dev/responsive-images/)
- [Image optimization best practices](https://web.dev/fast/#optimize-your-images)
- [Squoosh.app](https://squoosh.app) - Free online image optimizer

---

**Last Updated:** Based on diagnostics showing 17.65s LCP with 14.3 KB wasted data  
**Status:** Partial fix applied (explicit dimensions + fetch priority)  
**Next Action:** Generate optimized image assets using automation script
