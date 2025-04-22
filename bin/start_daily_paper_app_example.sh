#!/bin/bash
# 每日论文采集工具启动脚本
# 修改于 2025/4/22

# 设置环境变量
export SLACK_API_KEY="your_slack_api_key"
export WOLAI_APP_ID="your_wolai_app_id"
export WOLAI_APP_SECRETE="your_wolai_app_secret"
export WOLAI_TOKEN="your_wolai_token"
export WOLAI_DB_ID="your_wolai_db_id"
export NOTION_DB_ID="your_notion_db_id"
export NOTION_SECRET="your_notion_secret"

export KIMI_API_KEY="sk-your_kimi_api_key"
export KIMI_URL="https://api.moonshot.cn/v1"

export DEEPSEEK_URL="https://api.deepseek.com"
export DEEPSEEK_API_KEY="sk-your_deepseek_api_key"
export ZOTERO_USER_ID="your_zotero_user_id"
export ZOTERO_API_KEY="your_zotero_api_key"
export ZOTERO_LIBRARY_ID="your_zotero_library_id"

# 设置HTTP代理（如需使用）
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 设置日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 获取当前日期
CURRENT_DATE=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/daily_paper_$CURRENT_DATE.log"

# 检查是否使用conda环境
if command -v conda &> /dev/null; then
    echo "启用conda环境..."
    # 替换为你的conda环境名称
    CONDA_ENV="daily_paper_app"
    
    # 激活conda环境
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV"
    
    if [ $? -ne 0 ]; then
        echo "激活conda环境失败，尝试使用Python虚拟环境..."
        # 尝试使用Python虚拟环境
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
    fi
elif [ -d "venv" ]; then
    echo "启用Python虚拟环境..."
    source venv/bin/activate
fi

# 运行应用程序
echo "启动每日论文采集工具..."
echo "日志输出到: $LOG_FILE"

# 解析命令行参数
ARGS=""

# 处理输入参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --date=*)
            DATE="${1#*=}"
            ARGS="$ARGS --date $DATE"
            shift
            ;;
        --days=*)
            DAYS="${1#*=}"
            ARGS="$ARGS --days $DAYS"
            shift
            ;;
        --no-hf)
            ARGS="$ARGS --no-hf"
            shift
            ;;
        --no-arxiv)
            ARGS="$ARGS --no-arxiv"
            shift
            ;;
        --config=*)
            CONFIG="${1#*=}"
            ARGS="$ARGS --config $CONFIG"
            shift
            ;;
        --limit=*)
            LIMIT="${1#*=}"
            ARGS="$ARGS --limit $LIMIT"
            shift
            ;;
        *)
            echo "未知参数: $1"
            shift
            ;;
    esac
done

# 执行Python脚本并记录日志
python src/daily_paper_app.py $ARGS 2>&1 | tee -a "$LOG_FILE"

# 检查执行状态
RESULT=$?
if [ $RESULT -ne 0 ]; then
    echo "程序执行失败，错误代码: $RESULT" | tee -a "$LOG_FILE"
    # 发送失败通知
    # echo "发送失败通知..." | tee -a "$LOG_FILE"
    # 这里可以添加发送错误通知的命令，比如发邮件等
else
    echo "程序执行成功!" | tee -a "$LOG_FILE"
fi

# 退出conda或虚拟环境
if command -v conda &> /dev/null; then
    conda deactivate
elif [ -d "venv" ]; then
    deactivate
fi

exit $RESULT