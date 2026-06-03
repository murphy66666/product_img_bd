# OpenAI GPT Image 2 商品详情图生成

## 1. 接口地址

```bash
POST https://api.openai.com/v1/images/edits
```

------

## 2. curl 请求示例

```bash
curl --request POST \
  --url https://api.openai.com/v1/images/edits \
  --header "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  --header "Content-Type: multipart/form-data" \
  --form "model=gpt-image-2" \
  --form "image[]=@./product.jpg" \
  --form "prompt=基于上传的商品原图，生成4张专业电商商品详情图。要求：
1. 不改变商品主体外观
2. 分别生成：
   - 正面展示图
   - 45度侧面展示图
   - 顶部俯视展示图
   - 场景化展示图
3. 白色高级背景
4. 柔和商业摄影灯光
5. 高端电商品牌风格
6. 保持商品材质真实
7. 适合淘宝、京东、Amazon商品详情页
8. 超清细节
" \
  --form "size=1024x1024" \
  --form "n=4"
```

------

## 3. 参数说明

| 参数    | 类型    | 说明                    |
| ------- | ------- | ----------------------- |
| model   | string  | 使用的模型：gpt-image-2 |
| image[] | file    | 上传商品原图            |
| prompt  | string  | 商品详情图生成要求      |
| size    | string  | 输出尺寸                |
| n       | integer | 生成图片数量            |

------

## 4. 官方标准请求格式

请求 Content-Type：

```http
multipart/form-data
```

上传文件字段：

```http
image[]
```

这是 OpenAI 官方 Images Edit API 要求的格式。

------

## 5. 成功返回示例

```json
{
  "created": 1714783925,
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    },
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    },
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    },
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ]
}
```

------

## 6. b64_json 说明

返回的是：

```json
"b64_json"
```

即：

```text
Base64 编码后的图片数据
```

需要自行解码保存。

------

## 7. Linux/Mac 解码示例

假设返回内容保存为：

```bash
response.json
```

提取并保存第一张图：

```bash
cat response.json \
| jq -r '.data[0].b64_json' \
| base64 --decode > result1.png
```

第二张：

```bash
cat response.json \
| jq -r '.data[1].b64_json' \
| base64 --decode > result2.png
```

------

## 8. 商品图生成最佳实践

建议：

### 原图要求

- 白底
- 商品主体完整
- 清晰度高
- 尽量无阴影

### Prompt 要点

必须强调：

```text
不要改变商品主体
保持真实材质
商业摄影风格
电商详情页风格
```

否则模型可能会“创造性修改”商品。

------

## 9. 支持多张参考图

也可以上传多张参考图：

```bash
--form "image[]=@./front.jpg" \
--form "image[]=@./side.jpg"
```

这样生成稳定性更高。

------

## 10. 可选 mask 局部编辑

如果只想修改背景：

```bash
--form "mask=@./mask.png"
```

mask 白色区域会被重新生成。

------

## 11. 官方兼容接口

当前 GPT Image 2 使用：

```http
POST /v1/images/edits
```

兼容 OpenAI 官方 Images API 标准。

## 12.curl 上传图片



curl：

```bash
curl --request POST \
  --url https://api.openai.com/v1/images/edits \
  --header "Authorization: Bearer YOUR_API_KEY" \
  --form "model=gpt-image-2" \
  --form "image[]=@./product.jpg" \
  --form "prompt=生成电商商品详情图"
```

其中：

```bash
--form "image[]=@./product.jpg"
```

等价于：

```bash
上传一个文件字段
字段名=image[]
文件内容=product.jpg
```

## 13.实际 HTTP 请求格式

curl 实际发送的是：

```bash
POST /v1/images/edits HTTP/1.1
Host: api.openai.com
Authorization: Bearer sk-xxxx
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary
```

请求体：

```bash
------WebKitFormBoundary
Content-Disposition: form-data; name="model"

gpt-image-2
------WebKitFormBoundary
Content-Disposition: form-data; name="prompt"

生成电商商品详情图
------WebKitFormBoundary
Content-Disposition: form-data; name="image[]"; filename="product.jpg"
Content-Type: image/jpeg

<这里是真实图片二进制数据>
------WebKitFormBoundary--
```

重点：

```bash
图片会以二进制流形式发送
不是 base64
不是 JSON
```

## 14. OpenAI 服务端如何接收

OpenAI API 服务端会：

```bash
解析 multipart/form-data
↓
读取 image[] 文件字段
↓
识别图片格式
↓
送入 gpt-image-2 模型
```

## 15. 支持多个图片

可以：

```bash
--form "image[]=@./front.jpg" \
--form "image[]=@./side.jpg"
```

HTTP 会变成：

```bash
Content-Disposition: form-data; name="image[]"; filename="front.jpg"

Content-Disposition: form-data; name="image[]"; filename="side.jpg"
```

OpenAI 会收到：

```bash
image[] = [front.jpg, side.jpg]
```

## 16. Python 上传示例

```python
import requests

url = "https://api.openai.com/v1/images/edits"

files = {
    "image[]": open("product.jpg", "rb")
}

data = {
    "model": "gpt-image-2",
    "prompt": "生成商品详情图"
}

headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.post(
    url,
    headers=headers,
    files=files,
    data=data
)

print(response.json())
```

## 17. 不要这样传（错误方式）

不要：

```json
{
  "image": "base64xxxx"
}
```

Images Edit API 官方标准：

```json
必须 multipart/form-data
必须文件上传
```

不是 Chat Completions 的 JSON 格式。

## 18. GPT Image 2 的标准流程

```bash
本地图片文件
↓
multipart/form-data
↓
POST /v1/images/edits
↓
OpenAI API
↓
gpt-image-2
↓
返回 b64_json
```

