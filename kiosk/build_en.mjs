import { readFileSync, writeFileSync } from 'fs';
const dir = '/home/user/prompt-generator/kiosk/';
const src = readFileSync(dir + 'screens.html', 'utf8');

// balanced <div>...</div> extractor from an opening tag index
function extractDiv(html, startIdx) {
  const re = /<div\b|<\/div>/g; re.lastIndex = startIdx;
  let depth = 0, m, end = -1;
  while ((m = re.exec(html))) {
    if (m[0] === '<div') depth++;
    else { depth--; if (depth === 0) { end = m.index + 6; break; } }
  }
  return html.slice(startIdx, end);
}

// --- copy text (longer / more specific strings first) ---
const tr = [
  ['Оберіть страви', 'Choose your dishes'],
  ['Пошук у меню', 'Search the menu'],
  ['Переглянути замовлення', 'View order'],
  ['3 позиції', '3 items'],
  ['Налаштування позиції', 'Customize item'],
  ['Розмір порції', 'Portion size'],
  ['Додатки', 'Add-ons'],
  ['Додати · 260 ₴', 'Add · €12.20'],
  ['Ваше замовлення', 'Your order'],
  ['Додати ще позицію', 'Add another item'],
  ['До сплати', 'Total'],
  ['До меню', 'Back to menu'],
  ['До оплати', 'Checkout'],
  ['Оберіть спосіб оплати', 'Choose payment method'],
  ['Сума до сплати', 'Amount due'],
  ['Сума', 'Subtotal'],
  ['Знижка', 'Discount'],
  ['Банківська картка', 'Bank card'],
  ['Безконтактно / термінал', 'Contactless / terminal'],
  ['Готівка на касі', 'Cash at the counter'],
  ['QR-оплата', 'QR payment'],
  ['Оплатити 445 ₴', 'Pay €22.00'],
  ['Дякуємо, що обрали нас', 'Thanks for choosing us'],
  ['Замовлення прийнято!', 'Order accepted!'],
  ['Оплата пройшла успішно. Заберіть чек нижче.', 'Payment successful. Take your receipt below.'],
  ['Ваш номер замовлення', 'Your order number'],
  ['Готово за ~8 хв', 'Ready in ~8 min'],
  ['Слідкуйте за номером на екрані видачі', 'Watch for your number on the pickup screen'],
  ['Нове замовлення', 'New order'],
  ['Тут', 'Dine in'],  // badges/chips — applied last
];

// --- prices in EUR, per screen (same UAH string can mean different things per screen) ---
const priceMap = {
  s3: [ // menu cards, in DOM order: 85,120,65,140,95,110 ; bottom-bar total 270
    ['85 ₴','€4.50'], ['120 ₴','€6.90'], ['65 ₴','€2.90'],
    ['140 ₴','€7.90'], ['95 ₴','€5.50'], ['110 ₴','€5.90'],
    ['270 ₴','€14.00'],
  ],
  s4: [ // portion sizes 85/110/140, add-ons +20/+15 (button handled in tr)
    ['85 ₴','€3.90'], ['110 ₴','€4.90'], ['140 ₴','€5.90'],
    ['+20 ₴','+€1.20'], ['+15 ₴','+€0.90'],
  ],
  s5: [ // cart lines 260,120,65 ; subtotal/total 445 ; discount −0
    ['260 ₴','€12.20'], ['120 ₴','€6.90'], ['65 ₴','€2.90'],
    ['445 ₴','€22.00'], ['−0 ₴','−€0.00'],
  ],
  s6: [ ['445 ₴','€22.00'] ], // amount due (Pay button handled in tr)
  s7: [],
};

function translate(s, id) {
  for (const [a, b] of tr) s = s.split(a).join(b);
  for (const [a, b] of (priceMap[id] || [])) s = s.split(a).join(b);
  return s;
}

const caps = {
  s3: '3 · Menu — product selection',
  s4: '4 · Product — quantity & options',
  s5: '5 · Order confirmation',
  s6: '6 · Payment method',
  s7: '7 · Order accepted',
};

const head = src.slice(0, src.indexOf('<div class="gallery">') + '<div class="gallery">'.length);
let out = head.replace('<html lang="uk">', '<html lang="en">')
              .replace('<title>ECOFACTOR — Кіоск самообслуговування</title>',
                       '<title>ECOFACTOR Kiosk — English</title>');

let frames = '\n';
for (const id of ['s3','s4','s5','s6','s7']) {
  const start = src.indexOf(`<div class="screen" id="${id}">`);
  let block = extractDiv(src, start);
  block = block.replace(`id="${id}"`, `id="${id}en"`);
  block = translate(block, id);
  frames += `<div class="frame">\n  <div class="cap">${caps[id]}</div>\n  ${block}\n</div>\n\n`;
}

out += frames + '</div>\n</body>\n</html>\n';
writeFileSync(dir + 'screens_en.html', out);
console.log('screens_en.html built (EUR)');
