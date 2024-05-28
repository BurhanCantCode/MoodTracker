!pip install Flask pyngrok flask-socketio textblob openai

from flask import Flask, request, render_template_string
from pyngrok import ngrok
from flask_socketio import SocketIO
from textblob import TextBlob
from openai import AzureOpenAI
from google.colab import userdata

app = Flask(__name__)
socketio = SocketIO(app)

# Function to analyze mood based on text input
def analyze_mood(prompt):
    blob = TextBlob(prompt)
    sentiment_score = blob.sentiment.polarity

    if sentiment_score > 0.2:
        return "happy"
    elif sentiment_score < -0.2:
        return "sad"
    else:
        return "neutral"

# Azure OpenAI endpoint and deployment details
endpoint = "https://gpt4ohackathon.openai.azure.com/"
deployment_name = "gpt-4o"

# Create the AzureOpenAI client
client = AzureOpenAI(
    api_key=userdata.get("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=endpoint
)

# Function to generate advice using Azure OpenAI
def generate_advice(prompt):
    response = client.chat.completions.create(
        model=deployment_name,
        max_tokens=100,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that responds with cute human like emotions awww and stuff also it doesnt respond with continual texts like maybe i can do something it just gives a complete answer "},
            {"role": "user", "content": prompt}
        ]
    )

    # Check if the response is OK and return the advice
    if response and hasattr(response, 'choices') and len(response.choices) > 0:
        return response.choices[0].message.content.strip()
    else:
        return "No valid response received."

# HTML template
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mood Tracker</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0px 0px 30px rgba(0, 0, 0, 0.3); /* Increased box shadow */
            max-width: 800px;
            width: 100%;
            display: flex;
            flex-direction: row;
            justify-content: space-between;
        }
        .input-section {
            width: 45%;
            text-align: left;
        }
        .input-field {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            margin-bottom: 20px;
            font-size: 16px;
        }
        .emotion-bar {
            width: 100%;
            height: 20px;
            border-radius: 10px;
        }
        .advice-section {
            width: 45%;
            text-align: left;
            border-left: 1px solid #ccc;
            padding-left: 20px;
        }
        .btn {
            background-color: #007bff;
            color: #ffffff;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }
        .btn:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="input-section">
            <h1>Mood Tracker</h1>
            <input type="text" id="textInput" class="input-field" placeholder="Enter your text" autocomplete="off">
            <div id="emotionBar" class="emotion-bar"></div>
            <button id="getAdviceBtn" class="btn">Get Advice</button>
        </div>
        <div class="advice-section" id="adviceSection"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <script type="text/javascript">
        var socket = io();
        var input = document.getElementById("textInput");
        var emotionBar = document.getElementById("emotionBar");
        var getAdviceBtn = document.getElementById("getAdviceBtn");
        var adviceSection = document.getElementById("adviceSection");

        input.addEventListener("input", function() {
            socket.emit('text_input', {text: input.value});
        });

        getAdviceBtn.addEventListener("click", function() {
            socket.emit('generate_advice', {text: input.value});
        });

        socket.on('mood_result', function(msg) {
            var mood = msg.mood;
            // Map the mood to the color gradient in the emotion bar
            var color;
            switch (mood) {
                case 'happy':
                    color = '#32CD32'; // Green
                    break;
                case 'sad':
                    color = '#FF0000'; // Red
                    break;
                case 'neutral':
                    color = '#FFFF00'; // Yellow
                    break;
                default:
                    color = '#FFFFFF'; // White (default)
                    break;
            }
            emotionBar.style.background = color;
        });

        socket.on('advice_result', function(msg) {
            var advice = msg.advice;
            adviceSection.innerHTML = '<p>' + advice + '</p>';
        });
    </script>
</body>
</html>

"""

# Route for serving the HTML template
@app.route('/')
def index():
    return html

@app.route('/get_advice', methods=['POST'])
def get_advice():
    text = request.form['text']
    advice = generate_advice(text)
    return advice

@socketio.on('text_input')
def handle_text(data):
    text = data['text']
    mood = analyze_mood(text)
    socketio.emit('mood_result', {'mood': mood})

@socketio.on('generate_advice')
def handle_advice(data):
    text = data['text']
    advice = generate_advice(text)
    socketio.emit('advice_result', {'advice': advice})

# Start ngrok and expose the local server
public_url = ngrok.connect(5000)
print(f'Public URL: {public_url}')

# Run the Flask app with SocketIO
socketio.run(app, allow_unsafe_werkzeug=True)
