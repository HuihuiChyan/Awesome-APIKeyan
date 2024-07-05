import time
import openai
def get_response_turbo(messages, key=None, temp=0.5, stop="\n"):

    if key is not None:
        openai.api_key = key
    FailCnt = 0

    while(True):  
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature=temp,
                messages=messages,
                stop=stop,
            )
        except openai.error.RateLimitError:
            print("RateLimitError! Have a rest!")
            FailCnt +=1
            if FailCnt >= 10:
                print(f"The key {key} is failing!")
                return "INVALID KEY"
            time.sleep(1)
            continue
        except openai.error.APIError:
            print("APIError! Have a rest!")
            continue
        except openai.error.APIConnectionError:
            print("APIConnectionError! Have a rest!")
            continue
        except openai.error.Timeout:
            print("Timeout! Have a rest!")
            continue
        except openai.error.AuthenticationError:
            print("AuthenticationError! Have a rest!")
            FailCnt +=1
            if FailCnt >= 10:
                print(f"The key {key} is failing!")
                return "INVALID KEY"
            continue
        except openai.error.ServiceUnavailableError:
            print("ServiceUnavailableError! Have a rest!")
            continue            
        break
    
    result = response['choices'][0]['message']['content'].strip()
    return result

def get_response_gpt4(messages, key=None, temp=0.5, stop="\n"):

    import openai
    openai.api_base = "https://api_gpt4.ai-gaochao.com/v1"

    if key is not None:
        openai.api_key = key
    FailCnt = 0

    while(True):  
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-0613",
                temperature=temp,
                messages=messages,
                stop=stop,
            )
        except openai.error.RateLimitError:
            print("RateLimitError! Have a rest!")
            FailCnt +=1
            if FailCnt >= 10:
                print(f"The key {key} is failing!")
                return "INVALID KEY"
            time.sleep(1)
            continue
        except openai.error.APIError:
            print("APIError! Have a rest!")
            continue
        except openai.error.APIConnectionError:
            print("APIConnectionError! Have a rest!")
            continue
        except openai.error.Timeout:
            print("Timeout! Have a rest!")
            continue
        except openai.error.AuthenticationError:
            print("AuthenticationError! Have a rest!")
            FailCnt +=1
            if FailCnt >= 10:
                print(f"The key {key} is failing!")
                return "INVALID KEY"
            continue
        except openai.error.ServiceUnavailableError:
            print("ServiceUnavailableError! Have a rest!")
            continue            
        break
    
    result = response['choices'][0]['message']['content'].strip()
    return result