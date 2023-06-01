import time
import openai
def get_response_turbo(messages, key="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", temp=1.0, stop="\n"):

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
                return "INVALID KEY!"
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
                return "INVALID KEY!"
            continue
        break
    
    result = response['choices'][0]['message']['content'].strip()
    return result