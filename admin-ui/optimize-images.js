const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function optimizeAisinLogo() {
  const input = path.join(__dirname, 'public', 'AISIN_Logo.jpg');
  const outputDir = path.join(__dirname, 'public');

  if (!fs.existsSync(input)) {
    console.error('❌ Error: AISIN_Logo.jpg not found in public/ directory');
    process.exit(1);
  }

  console.log('🔧 Optimizing AISIN_Logo.jpg...');
  console.log('📦 Original file size:', (fs.statSync(input).size / 1024).toFixed(2), 'KB\n');

  try {
    // 1. Create right-sized JPEG (149×67) - matches display dimensions
    await sharp(input)
      .resize(149, 67, { 
        fit: 'contain', 
        background: { r: 255, g: 255, b: 255, alpha: 0 } 
      })
      .jpeg({ quality: 85, progressive: true })
      .toFile(path.join(outputDir, 'AISIN_Logo-149x67.jpg'));
    console.log('✅ Created AISIN_Logo-149x67.jpg (1x resolution)');

    // 2. Create WebP version (better compression)
    await sharp(input)
      .resize(149, 67, { 
        fit: 'contain', 
        background: { r: 255, g: 255, b: 255, alpha: 0 } 
      })
      .webp({ quality: 85 })
      .toFile(path.join(outputDir, 'aisin-logo.webp'));
    console.log('✅ Created aisin-logo.webp (1x resolution)');

    // 3. Create 2x retina JPEG version (298×134)
    await sharp(input)
      .resize(298, 134, { 
        fit: 'contain', 
        background: { r: 255, g: 255, b: 255, alpha: 0 } 
      })
      .jpeg({ quality: 85, progressive: true })
      .toFile(path.join(outputDir, 'AISIN_Logo-298x134.jpg'));
    console.log('✅ Created AISIN_Logo-298x134.jpg (2x resolution)');

    // 4. Create 2x retina WebP
    await sharp(input)
      .resize(298, 134, { 
        fit: 'contain', 
        background: { r: 255, g: 255, b: 255, alpha: 0 } 
      })
      .webp({ quality: 85 })
      .toFile(path.join(outputDir, 'aisin-logo@2x.webp'));
    console.log('✅ Created aisin-logo@2x.webp (2x resolution)');

    console.log('\n📊 File size comparison:\n');
    
    const files = [
      { name: 'AISIN_Logo.jpg', desc: 'Original (400×179)' },
      { name: 'AISIN_Logo-149x67.jpg', desc: '1x optimized JPEG (149×67)' },
      { name: 'aisin-logo.webp', desc: '1x optimized WebP (149×67)' },
      { name: 'AISIN_Logo-298x134.jpg', desc: '2x retina JPEG (298×134)' },
      { name: 'aisin-logo@2x.webp', desc: '2x retina WebP (298×134)' }
    ];

    let originalSize = 0;
    files.forEach(({ name, desc }) => {
      const filepath = path.join(outputDir, name);
      if (fs.existsSync(filepath)) {
        const stats = fs.statSync(filepath);
        const sizeKB = (stats.size / 1024).toFixed(2);
        console.log(`  ${name.padEnd(30)} ${sizeKB.padStart(8)} KB  (${desc})`);
        
        if (name === 'AISIN_Logo.jpg') {
          originalSize = stats.size;
        } else if (name === 'AISIN_Logo-149x67.jpg') {
          const saved = ((originalSize - stats.size) / 1024).toFixed(2);
          const percent = (((originalSize - stats.size) / originalSize) * 100).toFixed(1);
          console.log(`    → Saved ${saved} KB (${percent}% smaller than original)`);
        }
      }
    });

    console.log('\n🎯 Next Steps:');
    console.log('  1. Review the generated files in admin-ui/public/');
    console.log('  2. Update main.jsx to use the <picture> element (see IMAGE_OPTIMIZATION_GUIDE.md)');
    console.log('  3. Test in browser DevTools Network tab to verify size reduction');
    console.log('  4. Run Lighthouse audit to measure LCP improvement');
    console.log('\n✨ Optimization complete!\n');

  } catch (error) {
    console.error('❌ Error during optimization:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  optimizeAisinLogo().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { optimizeAisinLogo };
