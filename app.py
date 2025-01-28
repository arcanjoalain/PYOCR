from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS  # Importar Flask-CORS
import pytesseract
from PIL import Image
import os

# Configurando o Tesseract
#pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' # Windows
# # Ajuste conforme o caminho do Tesseract na sua máquina

app = Flask(__name__)

# Habilitar CORS no app Flask
CORS(app)

# Configuração do Swagger
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Diretório para salvar imagens temporariamente
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Nenhuma imagem enviada.'}), 400

        image = request.files['image']

        if not image.filename.lower().endswith(('png', 'jpg', 'jpeg')):
            return jsonify({'error': 'Formato de arquivo inválido. Use PNG ou JPG.'}), 400

        # Salvar a imagem
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(filepath)

        # Processar a imagem
        img = Image.open(filepath)

        # Executar OCR e identificar o dispositivo
        text = pytesseract.image_to_string(img)
        if "mg/dL" in text or "Glicose" in text:
            device = "Glicosímetro"
            data = extract_glicometer_data(img)
        elif "mmHg" in text or "Pressão" in text:
            device = "Medidor de Pressão"
            data = extract_pressure_monitor_data(img)
        else:
            device = "Desconhecido"
            data = {"error": "Não foi possível identificar os dados."}

        os.remove(filepath)
        return jsonify({'device': device, 'data': data}), 200

    except Exception as e:
        # Log do erro no terminal
        print(f"Erro ao processar a imagem: {str(e)}")
        return jsonify({'error': 'Erro ao processar a imagem.', 'details': str(e)}), 500

def extract_glicometer_data(image):
    """
    Extrai dados específicos de um glicosímetro.
    :param image: Imagem completa enviada.
    :return: JSON com os dados extraídos.
    """
    try:
        # Coordenadas específicas para a área do glicosímetro
        cropped_image = image.crop((50, 200, 400, 300))  # Ajustar conforme necessário
        data_text = pytesseract.image_to_string(cropped_image).strip()

        # Parse dos dados (exemplo)
        return {
            "glucose_level": data_text.split()[0],  # Exemplo: Primeiro valor como nível de glicose
            "unit": "mg/dL"
        }

    except Exception as e:
        return {"error": f"Erro ao extrair dados do glicosímetro: {str(e)}"}

def extract_pressure_monitor_data(image):
    """
    Extrai dados específicos de um medidor de pressão.
    :param image: Imagem completa enviada.
    :return: JSON com os dados extraídos.
    """
    try:
        # Coordenadas específicas para a área do medidor de pressão
        cropped_image = image.crop((50, 100, 400, 250))  # Ajustar conforme necessário
        data_text = pytesseract.image_to_string(cropped_image).strip()

        # Parse dos dados (exemplo)
        values = data_text.split()  # Supondo que os valores de pressão estejam separados
        return {
            "systolic": values[0],  # Primeiro valor como pressão sistólica
            "diastolic": values[1],  # Segundo valor como pressão diastólica
            "unit": "mmHg"
        }

    except Exception as e:
        return {"error": f"Erro ao extrair dados do medidor de pressão: {str(e)}"}

if __name__ == '__main__':
    app.run(debug=True)
