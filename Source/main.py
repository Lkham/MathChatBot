from flask import Flask, request, render_template
import json
import openai
import wolframalpha

WOLFRAM_APP_ID = '...'
OPENAI_API_KEY = '....'

client = wolframalpha.Client(WOLFRAM_APP_ID)

openai.api_key = OPENAI_API_KEY

def get_openai_response(myInput):
    completion = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        temperature = 0.2,
        max_tokens = 150,
        stop = [' Human:', ' AI:'],
        messages = [
            {"role": "system", "content": "You are a helpful assistant. However, if you're faced with a calculation or "
                                          "purely factual or analytical question suitable for Wolfram Alpha, delegate "
                                          "to Wolfram Alpha instead. Indicate this scenario by formatting the output "
                                          "exactly like this: Query for WolframAlpha: <query>"},
            {"role": "user", "content": myInput},
        ]
    )

    chatBotresponse = completion.choices[0].message.content

    if "Query for WolframAlpha:" in chatBotresponse:
        properWolframQuery = chatBotresponse.replace("Query for WolframAlpha:", "")
        return wolframQuery(properWolframQuery)
    else:
        return chatBotresponse

def wolframQuery(userInput):
    wolfram_res = client.query(userInput.strip(), params=(("format", "image, plaintext"),))
    for index, value in enumerate(wolfram_res.pods):
        if index == 1:
            for ind, s in enumerate(value.subpods):
                if ind == 0:
                    return s.img.src

def update_list(message, pl):
    pl.append(str(message))

def create_prompt(message, pl):
    user_msg = f'Human: {message}'
    update_list(user_msg, pl)
    prompt = ''.join(pl)
    return prompt

def get_bot_response(message, pl):
    prompt = create_prompt(message, pl)
    bot_response = get_openai_response(prompt)

    if bot_response:
        update_list(bot_response, pl)
    else:
        bot_response = 'Something went wrong ...'
    return bot_response


prompt_list = ["You are a helpful assistant. However, if you're faced with a calculation or "
                "purely factual or analytical question suitable for Wolfram Alpha, delegate "
                "to Wolfram Alpha instead. Indicate this scenario by formatting the output "
                "exactly like this: Query for WolframAlpha: <query>"]

app = Flask(
    __name__,
    static_url_path='/static',
    template_folder='./'
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "Hello! - Not connected to Dialogflow"
    elif request.method == 'POST':
        payload = request.json
        user_response = payload['queryResult']['queryText']
        print('User input: ' + user_response)
        bot_response = get_bot_response(user_response, prompt_list)
        print(f'Bot: {bot_response}')

        if user_response != '':
            res = {}
            if 'https:' in bot_response:
                res['fulfillmentMessages'] = [
                    {
                        'payload':{
                            'richContent':[
                                [
                                    {
                                        "type": "image",
                                        "rawUrl": (bot_response),
                                    }
                                ]
                            ]
                        }
                    }
                ]
            else:
                res['fulfillmentMessages'] = [
                    {
                        "text":{
                            "text":[
                                bot_response
                            ]
                        }
                    }
                ]
            return json.dumps(res)
    else:
        return '200'





if __name__ == "__main__":
    app.run(debug=True)









