import os
import random
import string
import sys
import datetime
from jinja2 import Template
import subprocess

# 可选：添加调试开关
DEBUG = True

def debug_print(*args):
    """打印调试信息，仅在 DEBUG=True 时生效"""
    if DEBUG:
        print("[DEBUG]", *args)

def ensure_directory_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        debug_print(f"目录 {directory} 不存在，已创建。")
    else:
        debug_print(f"目录 {directory} 已存在。")

def count_files_in_directory(directory):
    """统计目录中的文件数"""
    try:
        return sum(1 for entry in os.scandir(directory) if entry.is_file())
    except FileNotFoundError:
        debug_print(f"目录 {directory} 不存在，返回文件数 0")
        return 0
    except Exception as e:
        debug_print(f"统计文件数出错: {e}")
        raise

def generate_random_data():
    """生成随机数据"""
    now = datetime.datetime.now()
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return {
        'title': f"Title_{random_suffix}",
        'heading': f"Heading_{random_suffix}",
        'content': f"Content generated at {now.strftime('%H:%M:%S')}: {random_suffix}",
        'color': f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}',
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'generated_on': now.strftime('%Y-%m-%d')
    }

def generate_random_filename(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_code_file(directory, code_type):
    """生成指定类型的代码文件"""
    template_file = f"templates/{code_type}.jinja2"
    output_file = f"{directory}/{generate_random_filename()}.{code_type}"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    default_templates = {
        'js': "console.log('{{ data.heading }}');\nconsole.log('{{ data.content }}');",
        'html': "<!DOCTYPE html><html><head><title>{{ data.title }}</title></head><body><h1>{{ data.heading }}</h1><p>{{ data.content }}</p></body></html>",
        'css': "body { background-color: {{ data.color }}; }\nh1 { color: #{{ '%06X' % random.randint(0, 0xFFFFFF) }}; }",
        'py': """# {{ data.title }}
import random

def main():
    print("{{ data.heading }}")
    print("{{ data.content }}")

if __name__ == "__main__":
    main()
""",
        'json': """{
    "title": "{{ data.title }}",
    "heading": "{{ data.heading }}",
    "content": "{{ data.content }}",
    "metadata": {
        "created_at": "{{ data.created_at }}",
        "updated_at": "{{ data.updated_at }}"
    }
}""",
        'yaml': """---
title: {{ data.title }}
heading: {{ data.heading }}
content: {{ data.content }}
metadata:
  created_at: {{ data.created_at }}
  updated_at: {{ data.updated_at }}
""",
        'md': """# {{ data.heading }}

{{ data.content }}

*Generated on {{ data.generated_on }}*
"""
    }

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        debug_print(f"加载外部模板: {template_file}")
    except FileNotFoundError:
        template_content = default_templates.get(code_type, "/* No template available for {{ data.title }} */")
        debug_print(f"使用默认模板: {code_type}")
    except Exception as e:
        debug_print(f"加载模板出错: {e}")
        raise

    try:
        data = generate_random_data()
        code = Template(template_content).render(data=data)
        debug_print("生成的数据：", data)
        debug_print("渲染结果：\n", code)
    except Exception as e:
        debug_print(f"模板渲染出错: {e}")
        raise

    try:
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(code)
        print(f"✅ 生成文件: {os.path.basename(output_file)}")
    except Exception as e:
        debug_print(f"写入文件出错: {e}")
        raise

def remove_directory_contents(directory):
    """清空目录内容"""
    try:
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        print(f"🧹 目录 {directory} 已清空")
    except Exception as e:
        debug_print(f"清空目录出错: {e}")
        raise

def git_push_to_repo(token, repo_owner, repo_name, branch="main"):
    """推送更改到 GitHub 仓库（包含调试信息）"""
    try:
        print("🔧 设置 Git 用户信息...")
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions@github.com"], check=True)

        print("📦 添加更改...")
        subprocess.run(["git", "add", "."], check=True)

        print("📝 提交更改...")
        commit_result = subprocess.run(
            ["git", "commit", "-m", "Auto-generated code pushed"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if "nothing to commit" in commit_result.stdout.lower():
            print("ℹ️ 没有变更，跳过推送。")
            return

        print("🌍 设置远程仓库地址...")
        repo_url = f"https://{token}@github.com/{repo_owner}/{repo_name}.git"
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)

        print("🚀 推送中...")
        push_result = subprocess.run(
            ["git", "push", "origin", branch],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if push_result.returncode != 0:
            print("❌ 推送失败：")
            print("stdout:\n", push_result.stdout)
            print("stderr:\n", push_result.stderr)
        else:
            print("✅ 推送成功：")
            print("stdout:\n", push_result.stdout)

    except subprocess.CalledProcessError as e:
        print("❌ Git 命令执行失败：")
        print("命令:", e.cmd)
        print("返回码:", e.returncode)
        print("输出:", e.output)
        print("错误信息:", e.stderr)
    except Exception as e:
        print("🛑 未知错误：", e)

def main():
    """主函数：生成文件 + 自动推送"""
    if len(sys.argv) < 3:
        print("❗ 用法：python script.py 目录 文件数阈值")
        sys.exit(1)

    target_directory = sys.argv[1]
    try:
        threshold = int(sys.argv[2])
    except ValueError:
        print("❗ 文件数阈值必须是整数")
        sys.exit(1)

    ensure_directory_exists(target_directory)

    code_types = ["js", "html", "css", "py", "json", "yaml", "md"]
    generate_code_file(target_directory, random.choice(code_types))

    num_files = count_files_in_directory(target_directory)
    print(f"📄 当前文件数: {num_files}")

    if num_files > threshold:
        remove_directory_contents(target_directory)

    # === 自动推送部分 ===
    personal_token = os.getenv("PAT")
    repo_owner = os.getenv("USER")
    repo_name = os.getenv("REPO")

    if personal_token and repo_owner and repo_name:
        git_push_to_repo(personal_token, repo_owner, repo_name)
    else:
        print("⚠️ 缺少 PAT / USER / REPO 环境变量，跳过推送。")

if __name__ == "__main__":
    main()
