# 沙箱边界 POC

这个插件用于确认 MediaVault 第三方插件的真实运行边界，不执行上传、整理、删除或媒体库修改。

它固定探测：

- MoviePilot `192.168.50.99:3000` 的 HTTP 和 TCP 连接；
- `/volume1`、`/volume1/Link`、`/app`、`/config` 等路径；
- `app`、`mediavault`、`requests` 模块是否可见；
- 运行环境变量；
- 临时目录写入能力。

探测结果只通过插件 JSON 返回，不返回文件内容，不读取任何凭据。安装后可点击「执行探测」，也可等待 `strm.generated`、`media.uploaded` 或 `organize.completed` 事件触发。
