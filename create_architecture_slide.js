const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Connect Care';
pptx.subject = 'Personalized recipe recommendation flow';
pptx.title = 'Connect Care personalized recipe recommendation';
pptx.company = 'Connect Care';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US'
};
pptx.defineSlideMaster({
  title: 'MASTER',
  background: { color: 'F6F4EF' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.18, fill: { color: '1B5E5A' }, line: { color: '1B5E5A' } } },
    { text: { text: 'CONNECT CARE  /  RECIPE INTELLIGENCE', options: { x: 0.58, y: 7.12, w: 5.5, h: 0.2, fontFace: 'Aptos', fontSize: 8, bold: true, color: '6C7775', charSpacing: 1.2, margin: 0 } } }
  ],
  slideNumber: { x: 12.25, y: 7.08, color: '6C7775', fontFace: 'Aptos', fontSize: 8 }
});

const slide = pptx.addSlide('MASTER');
slide.addText('From recipe search to a personal recommendation', {
  x: 0.58, y: 0.5, w: 8.8, h: 0.55,
  fontFace: 'Aptos Display', fontSize: 25, bold: true, color: '173B3A', margin: 0
});
slide.addText('One request, two signals, one structured recipe response', {
  x: 0.6, y: 1.14, w: 7.5, h: 0.28,
  fontSize: 11.5, color: '65716E', margin: 0
});

function card(x, y, w, h, number, title, body, accent, footer) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: 'FFFFFF' }, line: { color: 'D8DFD9', width: 1.1 }, shadow: { type: 'outer', color: 'B9C2BC', blur: 1, angle: 45, distance: 1, opacity: 0.16 } });
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.11, h, fill: { color: accent }, line: { color: accent } });
  slide.addText(number, { x: x + 0.3, y: y + 0.25, w: 0.38, h: 0.28, fontSize: 12, bold: true, color: accent, margin: 0, align: 'center' });
  slide.addText(title, { x: x + 0.82, y: y + 0.22, w: w - 1.08, h: 0.32, fontSize: 15, bold: true, color: '173B3A', margin: 0 });
  slide.addText(body, { x: x + 0.3, y: y + 0.78, w: w - 0.58, h: 1.06, fontSize: 11.5, color: '465552', breakLine: false, valign: 'top', margin: 0.02, fit: 'shrink' });
  slide.addShape(pptx.ShapeType.line, { x: x + 0.3, y: y + h - 0.5, w: w - 0.6, h: 0, line: { color: 'E5EAE5', width: 1 } });
  slide.addText(footer, { x: x + 0.3, y: y + h - 0.35, w: w - 0.6, h: 0.18, fontSize: 9, bold: true, color: accent, margin: 0 });
}

card(0.58, 2.0, 3.35, 2.65, '01', 'Search server', 'Receives the user query and searches the multilingual JSONL recipe files with Jina embeddings.', '1B7F78', '127.0.0.1:7860');
card(4.98, 2.0, 3.35, 2.65, '02', 'User signal', 'Loads the latest calories_in value from the trajectory API summary for the selected user.', 'D17A45', '127.0.0.1:8000');
card(9.38, 2.0, 3.35, 2.65, '03', 'vLLM adapter', 'Combines the recipe, query, and calorie signal. Gemma scales or adapts the recipe and returns JSON.', 'C45755', '127.0.0.1:3960');

function arrow(x1, x2, y) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y, w: x2 - x1, h: 0, line: { color: '8A9993', width: 1.8, beginArrowType: 'none', endArrowType: 'triangle' } });
}
arrow(3.96, 4.82, 3.25);
arrow(8.36, 9.22, 3.25);

slide.addText('USER REQUEST', { x: 0.6, y: 5.12, w: 1.35, h: 0.18, fontSize: 9, bold: true, color: '1B7F78', charSpacing: 1.1, margin: 0 });
slide.addText('“apple dessert for 2 people”', { x: 0.6, y: 5.36, w: 3.75, h: 0.35, fontSize: 17, bold: true, italic: true, color: '173B3A', margin: 0 });
slide.addText('→', { x: 4.38, y: 5.29, w: 0.4, h: 0.35, fontSize: 22, bold: true, color: '8A9993', margin: 0, align: 'center' });

slide.addShape(pptx.ShapeType.roundRect, { x: 4.98, y: 5.02, w: 7.75, h: 1.05, rectRadius: 0.06, fill: { color: '173B3A' }, line: { color: '173B3A' } });
slide.addText('JSON RESPONSE', { x: 5.28, y: 5.23, w: 1.45, h: 0.16, fontSize: 8.5, bold: true, color: 'A8D8C9', charSpacing: 1, margin: 0 });
slide.addText('{ "...recipe fields": "...", "latest_calories_in": 2109, "updated_recipe": { ... } }', { x: 5.28, y: 5.53, w: 7.1, h: 0.24, fontFace: 'Courier New', fontSize: 11.5, color: 'FFFFFF', margin: 0, fit: 'shrink' });
slide.addText('The original recipe stays available; the personalized version is added under updated_recipe.', { x: 5.28, y: 6.0, w: 7.0, h: 0.2, fontSize: 9.5, color: 'C3D5CF', margin: 0 });

pptx.writeFile({ fileName: '/home/gaetano/projects/connect-care/connect-care-recommendation-flow.pptx' });
