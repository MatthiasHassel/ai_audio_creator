# AI-Audio-Creation-Tool

**Introduction**
*to do*

**Setup**
Make sure you have the latest version of Python3 installed on your system

Install llama3 via ollama: https://ollama.com/

Install packages from requirements.txt:
    cd /<your_project_directory_here>
    pip install -r requirements.txt

Adjust the .env_example file:
    Add your ElevenLabs API Key
    Add your Suno-Cookie and Session ID. Instructions for this: https://github.com/gcui-art/suno-api/blob/main/public/get-cookie-demo.gif

Rename the .env_example file to just .env
Make a copy of the .env file and put it in the suno_api directory   #temporary workaround. Should not be necessary in future versions
Install Suno API:
    cd /<your_project_directory_here>/suno_api
    npm install

To check if the Suno API works, in suno_api run: npm run dev
Visit http://localhost:3000/api/get_limit
If the following result is returned:
{
  "credits_left": 50,
  "period": "day",
  "monthly_limit": 50,
  "monthly_usage": 50
}
it means the program is running normally.


**Attributions**
Suno-API provided by: https://github.com/gcui-art/suno-api/tree/main

