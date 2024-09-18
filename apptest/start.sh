#!/bin/bash

# 定义颜色
GREEN="\033[1;32m"
RED="\033[1;31m"
BLUE="\033[1;34m"
RESET="\033[0m"

# 确保脚本有两个参数
if [ "$#" -ne 2 ]; then
    echo -e "${RED}[ERROR] 使用方法: $0 <deb包下载地址> <标识(一般为编号后四位)>${RESET}"
    exit 1
fi

# 获取参数
URL=$1
NEW_SUFFIX=$2

# 定义目录和文件名
DEST_DIR=.
FILE_NAME=$(basename "$URL")
NEW_FILE_NAME="${NEW_SUFFIX}.deb"
RESULT="${NEW_SUFFIX}.csv"
DEST_FILE="$DEST_DIR/$NEW_FILE_NAME"

# 创建目录（如果不存在的话）
mkdir -p "$DEST_DIR"

# 下载文件
echo -e "${BLUE}[INFO] 开始下载 $FILE_NAME...${RESET}"
wget --quiet --show-progress -O "$DEST_DIR/$FILE_NAME" "$URL"

# 检查下载是否成功
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] 下载 $FILE_NAME 失败${RESET}"
    exit 1
fi

echo -e "${GREEN}[ OK ] 下载成功${RESET}"

# 重命名文件
echo -e "${BLUE}[INFO] 重命名 $FILE_NAME 为 $NEW_FILE_NAME...${RESET}"
mv "$DEST_DIR/$FILE_NAME" "$DEST_FILE"

echo -e "${GREEN}[ OK ] 重命名成功${RESET}"


# 执行 Python 脚本
echo -e "${BLUE}[INFO] 对 $NEW_FILE_NAME 执行检测脚本...${RESET}"
python3 app_test.py -f "$DEST_FILE"

# 检查 Python 脚本是否执行成功
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] 脚本执行失败${RESET}"
    exit 1
fi

echo -e "${GREEN}[ OK ] 检测完成${RESET}"

mv "$NEW_FILE_NAME" $DEST_DIR/results/
mv "$RESULT" $DEST_DIR/results/

echo -e "${GREEN}[ OK ] 安装包和具体结果已存至./results目录${RESET}"
