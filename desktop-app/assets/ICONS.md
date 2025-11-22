# 图标资源

请在此目录放置应用图标文件：

- `icon.png` - 通用 PNG 图标 (512x512 推荐)
- `icon.icns` - macOS 图标
- `icon.ico` - Windows 图标

## 生成图标

可以使用在线工具或 `electron-icon-builder` 从 PNG 生成各平台图标：

```bash
npx electron-icon-builder --input=icon.png --output=./
```
