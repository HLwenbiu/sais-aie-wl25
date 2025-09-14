域名：https://gme-qwen2-vl-7b.ai4s.com.cn

### 文本 embedding

```bash
curl -X POST https://gme-qwen2-vl-7b.ai4s.com.cn/embed/text \
     -H "Content-Type: application/json" \
     -d '{"texts": ["测试文本"]}'
```

### 图像 embedding

```bash
curl -X POST https://gme-qwen2-vl-7b.ai4s.com.cn/embed/image \
     -H "Content-Type: application/json" \
     -d '{"images": ["base64编码的图像数据"]}'
```

### 多模态 embedding

```bash
curl -X POST https://gme-qwen2-vl-7b.ai4s.com.cn/embed/fused \
     -H "Content-Type: application/json" \
     -d '{"texts": ["测试文本"], "images": ["base64编码的图像数据"]}'
```

