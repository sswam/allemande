import cv2
import requests
import base64
import json

def cv2_img_to_img_api(cv2_img, access_key, model_type, **kwargs):
    # Convert cv2 image to base64 encoding
    _, buffer = cv2.imencode('.jpg', cv2_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    # Prepare API params
    params = {
        'model': model_type,
        'access_key': access_key,
        'data': img_base64,
        'datatype': 'base64',
        'prompt': kwargs.get('prompt', ''),
        'neg_prompt': kwargs.get('neg_prompt', ''),
        'cfg': kwargs.get('cfg', {}),
        'factor': kwargs.get('factor', 1),
        'time': kwargs.get('time', 0),
        'msg': kwargs.get('msg', ''),
        'type': kwargs.get('type', '')
    }

    # POST request to img2img API
    api_url = 'https://api.openai.com/v1/images/generations/ited/img'
    response = requests.post(api_url, json=params)

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return f"Error: {response.status_code} - {response.text}"

# Example usage
if __name__ == "__main__":
    cv2_img = cv2.imread("path/to/your/img.jpg")
    access_key = "your_access_key"
    model_type = "your_model_type"

    response = cv2_img_to_img_api(cv2_img, access_key, model_type,
                                  prompt="your_prompt",
                                  neg_prompt="your_neg_prompt",
                                  cfg={"key": "value"},
                                  factor=1,
                                  time=0,
                                  msg="string",
                                  type="string")
    print(response)
