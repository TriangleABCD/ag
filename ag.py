from openai import OpenAI
import subprocess
import argparse
import sys
from ag_utils import get_api_key, multi_line_input

# 常量配置模块
MODELS_CONFIG = {
    'deepseek': {
        'url': 'https://api.deepseek.com',
        'models': {
            'v3': 'deepseek-chat',
            'r1': 'deepseek-reasoner'
        }
    },
    'siliconflow': {
        'url': 'https://api.siliconflow.cn/v1',
        'models': {
            'v3': 'deepseek-ai/DeepSeek-V3',
            'r1': 'deepseek-ai/DeepSeek-R1'
        }
    }
}

ACTIVE_API = 'siliconflow'
BOT_ICONS = {
    'default': '🤖',
    'reasoner': '🤖🧐',
    'user': '🥰'
}

# 参数解析模块
def parse_arguments():
    """解析命令行参数"""
    default_model = MODELS_CONFIG[ACTIVE_API]['models']['v3']
    reasoner_model = MODELS_CONFIG[ACTIVE_API]['models']['r1']

    parser = argparse.ArgumentParser(description='Deepseek Agent')
    parser.add_argument('-r', '--reasoner',
                      action='store_const',
                      const=reasoner_model,
                      default=default_model,
                      dest='model',
                      help="使用深度推理模型")
    parser.add_argument('-c', '--chat',
                      action='store_true',
                      help="启用对话模式")
    parser.add_argument('-a', '--add',
                      action='store_true',
                      help="保留原始文本输出")
    parser.add_argument('-s', '--stream',
                      action='store_true',
                      help="启用流式输出")
    parser.add_argument('prompt', nargs='*')

    return parser.parse_args()

# 客户端初始化模块
def initialize_client(api_provider):
    """初始化OpenAI客户端"""
    config = MODELS_CONFIG[api_provider]
    return OpenAI(
        api_key=get_api_key(api_provider),
        base_url=config['url']
    )

# 命令执行模块
def execute_shell_command(command):
    """执行shell命令并返回结果"""
    try:
        result = subprocess.run(command,
                              shell=True,
                              text=True,
                              capture_output=True,
                              check=True)
        return result.stdout + '\n' + result.stderr
    except subprocess.CalledProcessError as e:
        return f"命令执行失败: {e}"

# 响应处理模块
def handle_stream_response(response, model_type, show_raw):
    """处理流式响应输出"""
    icon = BOT_ICONS['reasoner'] if model_type == 'r1' and not show_raw else BOT_ICONS['default']
    print(f'{icon}:')

    full_response = []
    for chunk in response:
        content = chunk.choices[0].delta.content or ""
        reasoning = chunk.choices[0].delta.reasoning_content or ""

        output = reasoning + content
        if output.strip():
            print(output, end="", flush=True)
            full_response.append(output)
    print("")
    return ''.join(full_response)

def handle_static_response(response, model_type, show_raw):
    """处理静态响应输出"""
    response_obj = response.choices[0].message
    if model_type == 'r1' and not show_raw:
        print(f"{BOT_ICONS['reasoner']}:\n{response_obj.reasoning_content}")
    print(f"{BOT_ICONS['default']}:\n{response_obj.content}")
    return response_obj.content

# 对话主逻辑
def chat_session(client, model, stream_enabled, show_raw):
    """处理对话会话"""
    messages = [{"role": "system", "content": "你是领域专家，从专业角度回答用户问题，优先考虑专业性"}]
    pre_input = ""

    model_type = 'r1' if 'reasoner' in model.lower() else 'v3'

    while True:
        print(f'{BOT_ICONS["user"]}:')
        if user_input := multi_line_input().strip():
            if user_input.lower() in ('exit', 'quit', 'q'):
                break

            if user_input.startswith('!'):
                command_output = execute_shell_command(user_input[1:])
                print(f"\n{command_output}")
                pre_input = command_output
                continue

            full_input = f"{pre_input} {user_input}".strip()
            messages.append({"role": "user", "content": full_input})

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream_enabled
            )

            if stream_enabled:
                response_content = handle_stream_response(response, model_type, show_raw)
            else:
                response_content = handle_static_response(response, model_type, show_raw)

            messages.append({"role": "assistant", "content": response_content})
            pre_input = ""

# 主执行流程
def main():
    args = parse_arguments()
    client = initialize_client(ACTIVE_API)
    initial_prompt = " ".join(args.prompt).strip()

    if args.chat:
        chat_session(client, args.model, args.stream, args.add)
    else:
        user_input = sys.stdin.read().strip()
        combined_input = f"{initial_prompt} {user_input}".strip()

        messages = [
            {"role": "system", "content": "你是领域专家，从专业角度回答用户问题，优先考虑专业性"},
            {"role": "user", "content": combined_input}
        ]

        response = client.chat.completions.create(
            model=args.model,
            messages=messages,
            stream=args.stream
        )

        if args.stream:
            handle_stream_response(response,
                                 'r1' if 'reasoner' in args.model else 'v3',
                                 args.add)
        else:
            handle_static_response(response,
                                 'r1' if 'reasoner' in args.model else 'v3',
                                 args.add)

if __name__ == "__main__":
    main()
