const sharp = require(process.env.FOLIO_SHARP || 'sharp');
const path = require('node:path');
sharp(path.resolve('assets/folio.svg')).resize(256, 256).png().toFile(path.resolve('assets/folio.png'))
  .then(() => console.log('Icon created')).catch(error => { console.error(error); process.exitCode = 1; });
