// Package the prepared artwork without redrawing it; PNG-backed multi-size Windows ICO.
const sharp = require(process.env.LILT_SHARP || 'sharp');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const sizes = [16, 24, 32, 48, 64, 128, 256];
  const source = path.resolve('assets/lilt-master.png');
  const pngs = await Promise.all(sizes.map(size => sharp(source).resize(size, size).png().toBuffer()));
  const header = Buffer.alloc(6 + 16 * sizes.length);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(sizes.length, 4);
  let offset = header.length;
  pngs.forEach((png, index) => {
    const entry = 6 + 16 * index;
    header[entry] = header[entry + 1] = sizes[index] === 256 ? 0 : sizes[index];
    header.writeUInt16LE(1, entry + 4);
    header.writeUInt16LE(32, entry + 6);
    header.writeUInt32LE(png.length, entry + 8);
    header.writeUInt32LE(offset, entry + 12);
    offset += png.length;
  });
  fs.writeFileSync(path.resolve('assets/lilt.ico'), Buffer.concat([header, ...pngs]));
  await sharp(source).resize(256, 256).png().toFile(path.resolve('assets/lilt.png'));
  fs.mkdirSync(path.resolve('frontend/src/assets'), {recursive: true});
  fs.copyFileSync(path.resolve('assets/lilt.png'), path.resolve('frontend/src/assets/lilt.png'));
  console.log('Created Lilt PNG and seven-size Windows icon.');
})().catch(error => { console.error(error); process.exitCode = 1; });
