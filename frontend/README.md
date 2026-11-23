# m10 前端工作台

前端是一个不依赖 CDN 的静态页面，由后端 FastAPI 以 `/static/` 路径托管。核心页面包括运行总览、数据导入与运行、曲线分析、异常记录、告警中心和运行记录。

## 页面约定

- 页面请求 `/api/health`、`/api/runs`、`/api/runs/{id}/overview`、`/api/runs/{id}/records` 和 `/api/runs/{id}/alerts`。
- CSV 导入使用 `POST /api/datasets/import?synthetic_demo=true|false`，再使用 `POST /api/runs` 提交 `dataset_id`、`k`、`contamination` 和 `mode`。
- 后端暂不可用时页面保留空状态和错误提示，不生成假结果。
- 图表使用内置 SVG 绘制，核心页面可在断网环境打开。
- 合成演示数据会在页面提示中明确标注。

## 本地调试

后端启动后访问 `http://127.0.0.1:8000/`。若后端使用其他地址，可在页面加载前设置 `window.M10_API_BASE`，或由后端统一托管静态资源。

## 文件

- `index.html`：页面结构与无障碍标签。
- `app.css`：响应式布局和视觉样式。
- `app.js`：API 请求、状态渲染、SVG 图表和 CSV 导出。
