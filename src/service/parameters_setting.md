# 配置文件说明

该配置文件用于设置脚本运行时的参数，包括关键词、日期和分类等。通过修改配置文件，您可以灵活地控制脚本的搜索行为。

以下是配置文件各参数的详细说明：

```json
{
    "keywords": [
      "reinforcement learning",
      ["power system", "eess.SY", "large language model"]
    ],
    "date": "",
    "categories": ["eess.SY", "cs.LG"]
}
```

## 参数说明

### 1. `keywords`（关键词）

- **类型**：列表，可以包含字符串或嵌套的列表。

- **作用**：指定搜索时使用的关键词条件。

- **详细说明**：

  - **单个关键词**：字符串形式，表示在论文的标题（title）或摘要（abstract）中搜索包含该关键词的论文。

    例如：

    ```json
    "keywords": ["reinforcement learning"]
    ```

    这将搜索标题或摘要中包含“reinforcement learning”的论文。

  - **嵌套关键词列表**：列表中包含子列表，子列表中的关键词使用 **OR** 逻辑连接，子列表与其他关键词之间使用 **AND** 逻辑连接。

    例如：

    ```json
    "keywords": [
      "reinforcement learning",
      ["power system", "large language model"]
    ]
    ```

    这将搜索标题或摘要中包含“reinforcement learning”，并且同时包含“power system”或“large language model”中的任意一个的论文。

- **示例**：

  - 搜索包含“机器学习”或“深度学习”的论文：

    ```json
    "keywords": [
      ["machine learning", "deep learning"]
    ]
    ```

  - 搜索包含“图像处理”，并且包含“神经网络”或“卷积”的论文：

    ```json
    "keywords": [
      "image processing",
      ["neural network", "convolution"]
    ]
    ```

### 2. `date`（日期）

- **类型**：字符串，格式为 `"YYYY-MM-DD"`，或者为空字符串 `""`。

- **作用**：指定搜索的日期，主要用于处理 Hugging Face 数据集的日期过滤。

- **详细说明**：

  - **指定日期**：当提供特定日期时，脚本将使用该日期进行处理。

    例如：

    ```json
    "date": "2024-09-23"
    ```

    这将使用 2024 年 9 月 23 日的数据。

  - **空字符串或省略**：如果未指定日期或为空字符串，脚本将使用当前日期。

    例如：

    ```json
    "date": ""
    ```

    或者直接省略 `date` 参数。

- **注意**：日期格式必须为 `"YYYY-MM-DD"`，否则可能导致脚本无法正确解析日期。

### 3. `categories`（分类）

- **类型**：字符串列表。

- **作用**：指定要搜索的 arXiv 分类代码，仅搜索这些分类下的论文。

- **详细说明**：

  - arXiv 分类代码由学科领域缩写和子领域缩写组成，例如：

    - `"cs.AI"`：计算机科学 - 人工智能
    - `"eess.SY"`：电子工程与系统科学 - 信号处理

  - 当指定分类列表时，搜索将仅限于这些分类中的论文。

- **示例**：

  - 搜索计算机视觉（cs.CV）和机器学习（cs.LG）领域的论文：

    ```json
    "categories": ["cs.CV", "cs.LG"]
    ```

  - 搜索物理学中的量子物理（quant-ph）：

    ```json
    "categories": ["quant-ph"]
    ```

## 综合示例

以下是一个综合的配置示例，结合关键词、日期和分类：

```json
{
    "keywords": [
      "deep learning",
      ["image recognition", "object detection"]
    ],
    "date": "2024-09-23",
    "categories": ["cs.CV", "cs.AI"]
}
```

这将搜索 2024 年 9 月 23 日，分类为计算机视觉（cs.CV）和人工智能（cs.AI）的论文，满足以下条件：

- 标题或摘要中包含“deep learning”，并且
- 标题或摘要中包含“image recognition”或“object detection”。

## 注意事项

- **关键词的逻辑关系**：

  - **同一级别的关键词之间**：默认使用 **AND** 逻辑连接。
  - **嵌套列表中的关键词**：使用 **OR** 逻辑连接。

- **分类过滤**：

  - 当指定了 `categories` 时，搜索范围将限定在这些分类内，有助于提高搜索效率，减少无关结果。

- **日期参数**：

  - 如果不需要特定日期，可以将 `date` 设置为空字符串 `""` 或者省略该参数，脚本将默认使用当前日期。

- **配置文件格式**：

  - 确保配置文件是合法的 JSON 格式，字符串使用双引号 `"`，不能使用单引号 `'`。
  - 列表和对象之间的逗号不能遗漏。

## 常见问题

1. **如何表示多个关键词的组合搜索？**

   - 使用嵌套列表来组合关键词，嵌套列表中的关键词使用 **OR**，与其他关键词之间使用 **AND**。

2. **我想搜索标题或摘要中包含“自然语言处理”或“NLP”的论文，应该如何设置？**

   ```json
   "keywords": [
     ["natural language processing", "NLP"]
   ]
   ```

3. **如果我不想限制分类，应该如何设置 `categories`？**

   - 将 `categories` 设置为 `null`，或者直接省略该参数。

   ```json
   "categories": null
   ```

4. **日期格式是否支持其他格式？**

   - 日期格式必须为 `"YYYY-MM-DD"`，这是标准的日期格式，脚本会按照此格式解析日期。
