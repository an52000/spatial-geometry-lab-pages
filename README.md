# 空间几何实验室

[打开实验室](https://an52000.github.io/spatial-geometry-lab-pages/) · [学习路线图](https://an52000.github.io/spatial-geometry-lab-pages/#roadmap)

这是实验室的独立静态发布仓库。学习进度保存在当前浏览器。MuJoCo 在浏览器中运行，Scene2 工作台用于核对记录和回算结果。

审查清单使用 `spatial-lab/pages-review/v1`，包含 `visibility: "public"`、`reviewed_by` 和 `files`。`files` 是从相对文件名到 SHA-256 的映射。核对内容授权和研究数据来源后再生成摘要。核验器会拒绝未审查的字节、额外文件以及检测到的本机路径、内部地址或私有包指纹。

审查后的静态文件和摘要清单一起提交并推送到 `main`。GitHub Actions 校验清单并上传 `pages-dist/`，在 `github-pages` 环境记录部署地址。
