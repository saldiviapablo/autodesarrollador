// ==============================================================================
// scripts/ensure-utf8-bom.js — Garantiza UTF-8 con BOM en todos los scripts .ps1
// ==============================================================================
const fs = require('fs');
const path = require('path');

const BOM = Buffer.from([0xEF, 0xBB, 0xBF]);

function ensureBomInFile(filePath) {
  const buf = fs.readFileSync(filePath);
  const hasBom = buf.length >= 3 && buf[0] === 0xEF && buf[1] === 0xBB && buf[2] === 0xBF;
  if (!hasBom) {
    fs.writeFileSync(filePath, Buffer.concat([BOM, buf]));
    console.log(`[BOM_ADDED] ${filePath}`);
    return true;
  } else {
    console.log(`[ALREADY_HAS_BOM] ${filePath}`);
    return false;
  }
}

function processDir(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const ent of entries) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      if (ent.name !== 'node_modules' && ent.name !== '.git' && ent.name !== 'data' && ent.name !== 'backups') {
        processDir(full);
      }
    } else if (ent.isFile() && ent.name.endsWith('.ps1')) {
      ensureBomInFile(full);
    }
  }
}

const infraRoot = path.resolve(__dirname, '..');
processDir(path.join(infraRoot, 'scripts'));
processDir(path.join(infraRoot, 'tests'));
console.log('UTF-8 BOM enforcement complete.');
