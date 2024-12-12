'''
Author: wds-Ubuntu22-cqu wdsnpshy@163.com
Date: 2024-12-12 16:41:50
Description: Setup configuration for the OpenAI Assistant package
'''
from setuptools import setup, find_packages
import os

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 从requirements.txt读取依赖
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="openai-wds-chat",
    version="0.1.0",
    author="wds-Ubuntu22-cqu",
    author_email="wdsnpshy@163.com",
    description="A flexible OpenAI API wrapper with multi-role support and context management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wds-dxh/openai-wds",  # 替换为您的GitHub仓库URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        'openai_wds_chat': [
            'config/*.json',
            'data/*.json',
        ],
    },
    entry_points={
        'console_scripts': [
            'openai-chat=src.main:main',  # 添加命令行入口点
        ],
    }
) 