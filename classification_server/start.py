from flask import Flask, jsonify, request
from flask_cors import CORS
from tools.train_model import train_model
from tools.get_predict import get_predict
from config import SERVER_PORT, PREDICT_API
import os
import asyncio

app = Flask(__name__)
CORS(app)
PORT = SERVER_PORT
API = PREDICT_API

model_path = "./model/model.joblib"

async def start():
    if not os.path.exists(model_path):
        print("Model not found")
        print("Starting the model training process")
        try:
            await train_model()

            try:
                print("Starting server")
                await app.run(port=PORT)
            except Exception as e:
                print(e)

        except Exception as e:
            print(e)
    else:
        print("Model found")
        print("Starting server")
        try:
            app.run(port=PORT)
        except Exception as e:
            print(e)


@app.route(API, methods=['POST'])
async def predict():
    data = request.get_json()

    if data is None:
        return jsonify({"error": "No input data provided"}), 400

    result = await get_predict(data["text"])

    return jsonify(result)

if __name__ == "__main__":
    asyncio.run(start())
