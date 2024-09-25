from setuptools import setup, find_packages

# 读取 requirements.txt 文件中的依赖项
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='PaperAssistant',
    version='1.0.0',
    packages=find_packages('src'),  # 指定源代码目录
    package_dir={'': 'src'},
    install_requires=requirements,  # 自动从 requirements.txt 中加载
    entry_points={
        'console_scripts': [
            'paper-assistant=daily_paper_app:main',  # 注册命令行入口
        ],
    },
)