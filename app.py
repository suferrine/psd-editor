from flask import Flask, request, send_file, render_template_string
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont
import io, os, json

app = Flask(__name__)
PSD_PATH = os.path.join(os.path.dirname(__file__), 'template.psd')
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Roboto-Black.ttf')

HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Редактор чека</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f0f2f5; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
  .card { background: #fff; border-radius: 12px; padding: 32px; width: 100%; max-width: 480px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); }
  h1 { font-size: 20px; margin-bottom: 24px; color: #1a1a2e; }
  label { display: block; font-size: 12px; color: #888; margin-bottom: 3px; margin-top: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  input { width: 100%; padding: 9px 12px; border: 1px solid #ddd; border-radius: 7px; font-size: 14px; outline: none; transition: border 0.2s; }
  input:focus { border-color: #4f8ef7; }
  button { margin-top: 24px; width: 100%; padding: 13px; background: #4f8ef7; color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; transition: background 0.2s; font-weight: bold; }
  button:hover { background: #2e6fe0; }
  button:disabled { background: #aaa; cursor: not-allowed; }
  .status { margin-top: 12px; font-size: 14px; color: #555; text-align: center; min-height: 20px; }
</style>
</head>
<body>
<div class="card">
  <h1>✏️ Редактор чека</h1>
  <form id="form">
    <label>Сумма (только цифры, напр. 500.000)</label>
    <input name="summa" value="9.374.120" required>

    <label>Валюта</label>
    <input name="valuta" value="ARS" required>

    <label>Банк</label>
    <input name="bank" value="Mercado Pago" required>

    <label>Комиссия (только цифры, напр. 335.000)</label>
    <input name="komis" value="335.000" required>

    <label>Номер счёта</label>
    <input name="schet" value="0000168300000025777411" required>

    <label>Имя получателя</label>
    <input name="imya" value="Baez Brenda Elizabeth" required>

    <label>Дата (во всех 3 местах сразу)</label>
    <input name="data" value="31/05/2026" required>

    <button type="submit" id="btn">⬇️ Скачать PNG</button>
  </form>
  <div class="status" id="status"></div>
</div>
<script>
document.getElementById('form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = document.getElementById('btn');
  const status = document.getElementById('status');
  btn.disabled = true;
  btn.textContent = '⏳ Генерирую...';
  status.textContent = '';
  try {
    const res = await fetch('/generate', { method: 'POST', body: new FormData(this) });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'check.png';
    a.click();
    status.textContent = '✅ Готово!';
  } catch(err) {
    status.textContent = '❌ Ошибка: ' + err.message;
  }
  btn.disabled = false;
  btn.textContent = '⬇️ Скачать PNG';
});
</script>
</body>
</html>
'''

def norm(vals):
    a, r, g, b = vals
    return (int(r*255), int(g*255), int(b*255), int(a*255))

def render(psd_path, font_path, summa, valuta, bank, komis, schet, imya, data):
    psd = PSDImage.open(psd_path)
    for layer in psd:
        if layer.kind == 'type':
            layer.visible = False
    bg = psd.composite().convert('RGBA')
    draw = ImageDraw.Draw(bg)

    def font(size):
        return ImageFont.truetype(font_path, int(size))

    def right(text, x2, y, size, c):
        f = font(size)
        bb = draw.textbbox((0,0), text, font=f)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        draw.text((x2 - tw, y), text, font=f, fill=norm(c))

    def left(text, x, y, size, c):
        f = font(size)
        draw.text((x, y), text, font=f, fill=norm(c))

    def center(text, x1, x2, y, size, c):
        f = font(size)
        bb = draw.textbbox((0,0), text, font=f)
        tw = bb[2] - bb[0]
        cx = x1 + (x2 - x1 - tw) // 2
        draw.text((cx, y), text, font=f, fill=norm(c))

    def multicolor(segments, x, y, size):
        f = font(size)
        cx = x
        for text, c in segments:
            draw.text((cx, y), text, font=f, fill=norm(c))
            bb = draw.textbbox((cx, y), text, font=f)
            cx += bb[2] - bb[0]

    W  = [1, 1,     1,     1    ]
    G  = [1, 0.525, 0.525, 0.525]
    P  = [1, 0.722, 0.384, 0.482]
    GR = [1, 0.294, 0.737, 0.408]

    # Сумма вверху - центр
    center(f"{summa} {valuta}",    163, 427, 160, 39.42, W)

    # Банк - правый край
    right(bank,                         566, 576, 20.42, W)

    # Валюта - правый край
    right(valuta,                       565, 608, 19.42, G)

    # Комиссия - правый край
    right(f"{komis} {valuta}",          563, 785, 21.42, P)

    # Дата справа - правый край
    right(data,                         562, 844, 19.42, W)

    # Номер счёта - правый край (было center, стало right)
    right(schet,                        535, 729, 19.42, W)

    # Имя - правый край
    right(imya,                         538, 667, 20.42, W)

    # Дата 1 - левый край
    left(data,  64, 322, 17, G)

    # Дата 2 - левый край
    left(data,  64, 404, 17, G)

    # Описание
    static = "Para que la transacción se lleve a cabo, es necesario pagar una"
    left(static, 62, 469, 15.42, W)
    multicolor([
        ("pago por el monto de ", W),
        (f"0 {valuta}",           P),
        ("/ ",                    W),
        (f"{komis} {valuta}",     GR),
    ], 62, 487, 15.42)

    out = io.BytesIO()
    bg.save(out, format='PNG')
    out.seek(0)
    return out

@app.route('/debug')
def debug():
    psd = PSDImage.open(PSD_PATH)
    result = []
    for layer in psd.descendants():
        if layer.kind == 'type':
            engine = layer.engine_dict
            info = {
                'name': str(layer.name),
                'text': str(layer.text),
                'bbox': list(layer.bbox),
                'visible': layer.visible
            }
            if 'StyleRun' in engine:
                run = engine['StyleRun']['RunArray'][0]
                if 'StyleSheet' in run:
                    sheet = run['StyleSheet']
                    info['style'] = {
                        'font': str(sheet.get('Font', '?')),
                        'size': str(sheet.get('FontSize', '?')),
                        'bold': str(sheet.get('FauxBold', False)),
                        'color': str(sheet.get('FillColor', '?'))
                    }
            result.append(info)
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    summa  = request.form.get('summa',  '')
    valuta = request.form.get('valuta', '')
    bank   = request.form.get('bank',   '')
    komis  = request.form.get('komis',  '')
    schet  = request.form.get('schet',  '')
    imya   = request.form.get('imya',   '')
    data   = request.form.get('data',   '')

    out = render(PSD_PATH, FONT_PATH, summa, valuta, bank, komis, schet, imya, data)
    return send_file(out, mimetype='image/png', download_name='check.png')

if __name__ == '__main__':
    app.run(debug=True)
