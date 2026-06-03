根据您提供的 OpenAI API 官方文档页面，以下是针对 **Create image (创建图片)** 接口规范且详细的 API 接口文档：

# OpenAI API 接口文档：创建图片 (Create image)

> 接口网址：https://developers.openai.com/api/reference/resources/images/methods/generate

## 1. 接口概述

- **描述**：根据给定的文本提示词（Prompt）创建/生成一张或多张图片。
- **HTTP 请求方法**：`POST`
- **请求 URL**：`https://api.openai.com/v1/images/generations`
- **Content-Type**：`application/json`
- **认证方式**：需要在 Header 中携带 Bearer Token (`Authorization: Bearer $OPENAI_API_KEY`)

## 2. 请求参数 (Request Body)

请求体为 JSON 格式，包含以下参数：

| **参数名称**           | **类型** | **是否必选** | **默认值** | **说明**                                                     |
| ---------------------- | -------- | ------------ | ---------- | ------------------------------------------------------------ |
| **prompt**             | string   | **是**       | -          | 对期望生成图片的文本描述。最大长度限制：GPT 图像模型为 32,000 字符；`dall-e-3` 为 4000 字符；`dall-e-2` 为 1000 字符。 |
| **model**              | string   | 否           | `dall-e-2` | 要使用的图像生成模型。可选值：`dall-e-2`, `dall-e-3` 以及 GPT 图像模型 (`gpt-image-1`, `gpt-image-1-mini`, `gpt-image-1.5`)。若使用了 GPT 图像模型特有参数，则默认转向对应模型。 |
| **n**                  | number   | 否           | 1          | 生成图片的数量。必须在 1 到 10 之间。注意：`dall-e-3` 仅支持 `n=1`。 |
| **size**               | string   | 否           | -          | 生成图片的尺寸。各模型支持详情见下方**[尺寸说明]**。         |
| **quality**            | string   | 否           | `auto`     | 图像生成的质量。可选值：`auto` (自动选择最佳), `low`, `medium`, `high` (后三者仅支持 GPT 图像模型)；`standard`, `hd` (支持 `dall-e-3`)；`dall-e-2` 仅支持 `standard`。 |
| **response_format**    | string   | 否           | `url`      | 图片返回的格式。可选值：`url` (链接) 或 `b64_json` (Base64 编码)。**注意**：生成的 URL 有效期为 60 分钟。GPT 图像模型不支持此参数，它们总是返回 Base64 编码。 |
| **style**              | string   | 否           | `vivid`    | 图像的风格。**仅支持 `dall-e-3`**。可选值：`vivid`（偏向生成超写实、戏剧化的图像）或 `natural`（偏向生成更自然、较少夸张修饰的图像）。 |
| **background**         | string   | 否           | `auto`     | 设置生成图片的背景透明度。**仅支持 GPT 图像模型**。可选值：`transparent` (透明), `opaque` (不透明), `auto` (自动)。若设为 `transparent`，`output_format` 必须设为支持透明度的 `png` 或 `webp`。 |
| **output_format**      | string   | 否           | `png`      | 返回图片的格式。**仅支持 GPT 图像模型**。可选值：`png`, `jpeg`, `webp`。 |
| **output_compression** | number   | 否           | 100        | 图片的压缩率（0-100%）。**仅支持 GPT 图像模型**且配合 `webp` 或 `jpeg` 格式使用。 |
| **stream**             | boolean  | 否           | `false`    | 是否开启流式传输模式生成图片。**仅支持 GPT 图像模型**。      |
| **partial_images**     | number   | 否           | -          | 在流式响应中返回部分/切片图片的数量。必须在 0 到 3 之间。若为 0，则在单个流式事件中发送完整图片。 |
| **moderation**         | string   | 否           | `auto`     | 控制 GPT 图像模型生成图片的内容审核严格程度。可选值：`low`（较宽松的过滤）或 `auto`。 |
| **user**               | string   | 否           | -          | 代表终端用户的唯一标识符，可帮助 OpenAI 监控和检测滥用行为。 |

### [尺寸说明 (size)]

- **GPT 图像模型 (`gpt-image-2`系列)**：支持自定义分辨率，格式为 `宽度x高度`（如 `1536x864`）。宽高必须是 16 的倍数，宽高比需在 1:3 到 3:1 之间。最高支持 `3840x2160`（2560x1440 以上为实验性）。同样支持标准尺寸 `1024x1024`, `1536x1024`, `1024x1536`。
- **dall-e-2**：可选 `256x256`, `512x512`, `1024x1024`。
- **dall-e-3**：可选 `1024x1024`, `1792x1024`, `1024x1792`。

## 3. 返回响应 (Response Body)

返回一个包含 `ImagesResponse` 对象的 JSON。

### 属性说明

- **created** (number): 图片创建时的 Unix 时间戳（秒）。
- **background** (string, 可选): 图像生成使用的背景类型（`transparent` 或 `opaque`）。
- **output_format** (string, 可选): 图片的输出格式（`png`, `webp`, `jpeg`）。
- **quality** (string, 可选): 生成的图片质量（`low`, `medium`, `high`）。
- **size** (string, 可选): 图片的尺寸（如 `1024x1024`）。
- **data** (array): 包含生成图片对象的数组，每个对象包含：
  - `url` (string): 图片的 Web URL 链接（主要用于 DALL-E 模型）。
  - `b64_json` (string): Base64 编码的图片数据（GPT 图像模型默认返回）。
  - `revised_prompt` (string): **仅限 `dall-e-3`**，模型在生成图片前自动修改优化后的最终提示词。
- **usage** (object, 可选): **仅限 `gpt-image-1`**，包含本次图片生成的 Token 消耗统计：
  - `input_tokens` / `output_tokens` / `total_tokens` (number)
  - `input_tokens_details` / `output_tokens_details` (object): 细分为 `image_tokens`（图像 Token）和 `text_tokens`（文本 Token）。

## 4. 请求与返回示例

### 示例 1：常规非流式请求 (以 GPT-1.5 为例)

#### cURL 请求示例

Bash

```
curl https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-image-1.5",
    "prompt": "A cute baby sea otter",
    "n": 1,
    "size": "1024x1024"
  }'
```

#### JSON 返回示例 (200 OK)

JSON

```
{
  "created": 1713833628,
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ],
  "usage": {
    "total_tokens": 100,
    "input_tokens": 50,
    "output_tokens": 50,
    "input_tokens_details": {
      "text_tokens": 10,
      "image_tokens": 40
    }
  }
}
```

### 示例 2：流式请求 (Stream Mode)

#### cURL 请求示例

Bash

```
curl https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-image-1.5",
    "prompt": "A cute baby sea otter",
    "n": 1,
    "size": "1024x1024",
    "stream": true
  }' \
  --no-buffer
```

#### SSE (Server-Sent Events) 流式返回示例

Plaintext

```
event: image_generation.partial_image
data: {"type":"image_generation.partial_image","b64_json":"...","partial_image_index":0}

event: image_generation.completed
data: {"type":"image_generation.completed","b64_json":"...","usage":{"total_tokens":100,"input_tokens":50,"output_
```