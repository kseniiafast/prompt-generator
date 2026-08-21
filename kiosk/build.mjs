import { readFileSync, writeFileSync } from 'fs';

const dir = '/home/user/prompt-generator/kiosk/';
const fonts = readFileSync(dir + 'fonts.css', 'utf8');
const screensHtml = readFileSync(dir + 'screens.html', 'utf8');
let tpl = readFileSync(dir + 'gallery_template.html', 'utf8');

const labels = {
  s1: 'Стартовий екран',
  s2: 'Тип замовлення',
  s3: 'Меню — вибір продукту',
  s4: 'Продукт — кількість та опції',
  s5: 'Підтвердження замовлення',
  s6: 'Вибір способу оплати',
  s7: 'Замовлення прийнято',
};

// extract a balanced <div ...> ... </div> starting at index of the opening tag
function extractDiv(html, startIdx) {
  // startIdx points at '<div' opening of the screen
  let i = startIdx;
  let depth = 0;
  const re = /<div\b|<\/div>/g;
  re.lastIndex = startIdx;
  let m;
  let end = -1;
  while ((m = re.exec(html))) {
    if (m[0] === '<div') depth++;
    else { depth--; if (depth === 0) { end = m.index + '</div>'.length; break; } }
  }
  return html.slice(startIdx, end);
}

let devices = '';
const ids = ['s1','s2','s3','s4','s5','s6','s7'];
ids.forEach((id, idx) => {
  const marker = `<div class="screen" id="${id}">`;
  const start = screensHtml.indexOf(marker);
  if (start === -1) throw new Error('not found ' + id);
  let block = extractDiv(screensHtml, start);
  // rename collision-prone classes used inside screens
  block = block.replace(/class="grid"/g, 'class="grid2"')
               .replace(/class="foot"/g, 'class="foot2"');
  const n = String(idx + 1).padStart(2, '0');
  devices += `    <div class="device">
      <div class="devlabel"><span class="n">${n}</span><span class="t">${labels[id]}</span></div>
      <div class="screenbox">${block}</div>
    </div>\n`;
});

tpl = tpl.replace('/*FONTS_PLACEHOLDER*/', fonts);
tpl = tpl.replace('<!--SCREENS_PLACEHOLDER-->', devices);
writeFileSync(dir + 'index.html', tpl);
console.log('index.html built, bytes:', tpl.length);
