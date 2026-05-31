from flask import Flask, request, send_file, render_template_string
from psd_tools import PSDImage
from psd_tools.psd.engine_data import String as EngineString
import io, os

app = Flask(__name__)
PSD_PATH = os.path.join(os.path.dirname(__file__), 'template.psd')

HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PSD Editor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f0f2f5; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
  .card { background: #fff; border-radius: 12px; padding: 32px; width: 100%; max-width: 480px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); }
  h1 { font-size: 22px; margin-bottom: 24px; color: #1a1a2e; }
  label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; margin-top: 14px; }
  input { width: 100%; padding: 9px 12px; border: 1px solid #ddd; border-radius: 7px; font-size: 14px; outline: none; transition: border 0.2s; }
  input:focus { border-color: #4f8ef7; }
  button { margin-top: 24px; width: 100%; padding: 12px; background: #4f8ef7; color: #fff; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: background 0.2s; }
  button:hover { background: #2e6fe0; }
  button:disabled { background: #aaa; cursor: not-allowed; }
  .status { margin-top: 14px; font-size: 14px; color: #555; text-align: center; min-height: 20px; }
</style>
</head>
<body>
<div class="card">
  <h1>✏️ Редактор чека</h1>
  <form id="form">
    <label>Имя получателя</label>
    <input name="name" value="Baez Brenda Elizabeth" required>

    <label>Дата (3 поля одновременно)</label>
    <input name="date" value="31/05/2026" required>

    <label>Сумма</label>
    <input name="amount" value="335.000 ARS" required>

    <label>Номер транзакции</label>
    <input name="transaction" value="0000168300000025777411" required>

    <label>Валюта</label>
    <input name="currency" value="ARS" required>

    <label>Банк</label>
    <input name="bank" value="Mercado Pago" required>

    <label>Баланс</label>
    <input name="balance" value="9.374.120 ARS" required>

    <label>Текст описания (строка 1)</label>
    <input name="desc1" value="Para que la transacción se lleve a cabo, es necesario pagar una">

    <label>Текст описания (строка 2)</label>
    <input name="desc2" value="pago por el monto de 0 ARS/ 335.000 ARS">

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
  const data = new FormData(this);
  try {
    const res = await fetch('/generate', { method: 'POST', body: data });
    if (!res.ok) { throw new Error(await res.text()); }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'result.png';
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

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    name     = request.form.get('name', '')
    date     = request.form.get('date', '')
    amount   = request.form.get('amount', '')
    txn      = request.form.get('transaction', '')
    currency = request.form.get('currency', '')
    bank     = request.form.get('bank', '')
    balance  = request.form.get('balance', '')
    desc1    = request.form.get('desc1', '')
    desc2    = request.form.get('desc2', '')

    psd = PSDImage.open(PSD_PATH)
    layers = list(psd)

    def set_text(idx, text, trail='\r'):
        layers[idx].engine_dict['Editor']['Text'] = EngineString(text + trail)

    set_text(1,  name,     '\r\r\r')
    set_text(2,  date,     '')
    set_text(3,  date,     '')
    set_text(4,  date,     '')
    set_text(5,  amount,   '')
    set_text(6,  txn,      '')
    set_text(7,  currency, '')
    set_text(8,  bank,     '')
    set_text(9,  balance,  '')
    layers[11].engine_dict['Editor']['Text'] = EngineString(desc1 + '\r' + desc2)

    buf = io.BytesIO()
    psd.save(buf)
    buf.seek(0)

    psd2 = PSDImage.open(buf)
    img = psd2.composite()

    out = io.BytesIO()
    img.save(out, format='PNG')
    out.seek(0)

    return send_file(out, mimetype='image/png', download_name='result.png')

if __name__ == '__main__':
    app.run(debug=True)
