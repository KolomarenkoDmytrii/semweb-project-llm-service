# LLM service for SemWeb Chemistry REST API Project

## Install and setup KoboldCpp

Follow instruction [here](https://github.com/LostRuins/koboldcpp#download-and-run) for installation guide.

Then run executable (`koboldcpp-linux-x64` for Linux, `koboldcpp-mac-arm64` for macOS and `koboldcpp.exe` for Windows) and choose the model. The app was tested with `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf` (a larger file, 4.22 GB in size) model from https://huggingface.co/unsloth/gemma-4-E4B-it-qat-GGUF/tree/main.

## API reference

- POST `/llm/v1/chat`: accepts JSON in the request body with the following fields:
    - `"message"`: User's prompt
    - `"conversation_id"`: a string identificator of the conversation / chat. Used for storing the context between requests.
    - Returns:
        - `"response"`: A response from the model.
        - `"conversation_id"`: a string identificator of the conversation / chat.
- GET `/llm/v1/health`: check health of the service. Returns a JSON in the response body:
    - `"status"`: `"ok"` when the service is healthy and works.
    - `"agent_initialized"`: Is the LLM agent initialized?
    - `"chemistry_api"`: URL to Chemistry Wikidata API.
    - `"kobold_api"`: URL to KoboldCpp instance.

## How to run a service

In the root project directory run this command: `uvicorn src.main:app --port 3000 --reload`. And then you can reference it, for example, on a local device through http://127.0.0.1:3000 URL (http://127.0.0.1:3000/docs for API Swagger documentation).
