from openai import OpenAI
import subprocess
import argparse
import sys
from ag_utils import get_api_key, multi_line_input


models_const = {
    'deepseek': {
        'url': 'https://api.deepseek.com',
        'v3': 'deepseek-chat',
        'r1': 'deepseek-reasoner'
    },
    'siliconflow': {
        'url': 'https://api.siliconflow.cn/v1',
        'v3': 'deepseek-ai/DeepSeek-V3',
        'r1': 'deepseek-ai/DeepSeek-R1'
    }
}

api_chose = 'deepseek'


parser = argparse.ArgumentParser(description='Deepseek Agent')
parser.add_argument('-r', '--r1', action='store_const',
                    const=models_const[api_chose]['r1'],
                    default=models_const[api_chose]['v3'],
                    dest='model', help="使用 deepseek-reasoner 模型")
parser.add_argument('-c', '--chat', action='store_true', dest='chat', help="对话形式")
parser.add_argument('-a', '--add', action='store_true', dest='add', help="输出原文")
parser.add_argument('-s', '--stream', action='store_true', dest='stream', help="流式输出")
parser.add_argument('non_option_args', nargs='*')
args = parser.parse_args()


api_key = get_api_key(api_chose)

client = OpenAI(
    api_key=api_key,
    base_url=models_const[api_chose]['url']
)
model = args.model


messages = [
    {"role": "system", "content": "你是领域专家，从专业角度回答用户问题，优先考虑专业性"}
]
pre_input = " ".join(args.non_option_args)


if args.chat:
    while True:
        print('🥰:')
        user_input = multi_line_input()
        if user_input == 'exit' or user_input == 'quit' or user_input == 'q':
            break

        if user_input.startswith('!'):
            print('命令执行成功')
            command = user_input[1:]
            pre_input = ''
            try:
                result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
                pre_input = result.stdout + '\n' + result.stderr
                print(pre_input)
            except subprocess.CalledProcessError as e:
                print('命令执行失败:', e)
            continue

        user_input = pre_input + ' ' + user_input
        messages.append({"role": "user", "content": user_input})
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=args.stream
        )
        print('')
        cur_content = ""
        if args.stream:
            if model == 'deepseek-reasoner' and (not args.add):
                print('🤖🧐:')
            else:
                print("🤖:")
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    cont = chunk.choices[0].delta.content
                    if cont == 'data: [DONE]':
                        break
                    print(cont, end="", flush=True)
                    cur_content += cont
            print('')
        else:
            if model == models_const[api_chose]['r1']:
                print('🤖🧐:\n' + response.choices[0].message.reasoning_content)
            print('🤖:\n' + response.choices[0].message.content)
            cur_content = response.choices[0].message.content
        messages.append({"role": "system", "content": cur_content})

else:
    user_input = sys.stdin.read()
    if args.add:
        print(user_input)
    else:
        print('🥰:')
    user_input = pre_input + ' ' + user_input

    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=args.stream
    )
    print('')
    if args.stream:
        if model == 'deepseek-reasoner' and (not args.add):
            print('🤖🧐:')
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                if chunk.choices[0].delta.content == 'data: [DONE]':
                    break
                print(chunk.choices[0].delta.content, end="", flush=True)

    else:
        if model == 'deepseek-reasoner' and (not args.add):
            print('🤖🧐:\n' + response.choices[0].message.reasoning_content)
        if not args.add:
            print('🤖:\n')
        print(response.choices[0].message.content)
