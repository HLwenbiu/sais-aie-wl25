# SAIS AI Engineering Group Warmup Lab 2025

## 实验要求

开发一个带有RAG的Multi-Agent心内科疾病诊断系统：

1. 系统示例输入见`medical_records`文件夹

2. 系统示例输出见`output_example.json`

3. 搭建一套RAG系统，所使用的语料见`corpus`文件夹

4. Multi-Agent需要至少包括三个Agent，至少一个Agent需要与RAG结合，这里给出一个包含三个Agent的Multi-Agent示例（仅作参考，具体实现时可自行设计）：

   - `Dr.Hypothesis`：根据患者病历信息生成生成诊断假设列表
   - `Dr.Challenger`：对诊断假设列表进行分析，检查是否存在诊断误差并提出替代诊断
   - `Dr.Clinical-Reasoning`：综合给出信息完成诊断，生成符合要求格式的主/次要诊断和鉴别诊断

5. 最终提交的服务必须使用docker进行容器化，请使用dockerfile进行docker镜像的构建

6. 最终实现的系统需要支持`curl`调用：

   1. 示例调用：

      ```bash
      curl -X POST "http://localhost:8080/cardiomind" -H "Content-Type: application/json" --data-binary "@case1.json"
      ```

   2. 返回结果：见`example.json`

7. 开发过程中请使用Git进行项目管理，并将代码托管在Github，请在模块完成或者版本更新时进行提交，确保最终的commit记录能够清晰地表明项目开发的流程

## LLM使用

- 本次Lab向同学们提供DeepSeek-V3模型，具体调用方式请查询[JuheNet](https://docs.juhenext.com/cn/introduction.html)，调用模型名称为`deepseek-v3-0324`
- 每位同学拥有约200万tokens的额度
- LLM调用API KEY会由@miaozeyun发给每位同学

## 提交内容

请在Lab仓库中创建独立的`final`分支进行提交，具体需要提交的内容包括：

1. `Readme.md`文件：说明如何使用`姓名-Cardiomind-Agent.tar`文件在任何一台安装了docker的机器上将服务启动并进行测试，其中`姓名-Cardiomind-Agent.tar`文件是由docker镜像保存得到的`.tar`格式的归档包
2. `Presentation.ppt/pptx`文件：说明该系统的具体实现细节，需要贴出在项目的开发过程中阅读的论文，文档，博客等材料

请在Lab截止时间前将`姓名-Cardiomind-Agent.tar`文件发送到邮箱`zymiao24@m.fudan.edu.cn`（姓名使用拼音全拼即可）

## 截止时间

**2025年9月14日24:00**

在截止时间后的git commit不会被视为有效的commit，距离截止时间最近的一次commit会被视为你本次Lab的最终提交，同样的距离截止时间最近的一次发送到邮箱`zymiao24@m.fudan.edu.cn`中的`姓名-Cardiomind-Agent.tar`文件会被用于Lab Pre时的现场演示。

## 提问

- 每位同学有三次向@miaozeyun提问的机会，任何和项目有关的问题，包括某些环节可以采用什么样的技术、具体的代码如何实现、出现了这样的Bug应该如何解决等
- Lab本意是希望同学们了解AI工程组某个现有项目的主要流程及Agent应用开发的各个环节，对于同学们的实现效果并没有要求，所以还是希望同学们能够独自完成技术选型、代码开发及调试、部署及测试等工作，不要将希望寄托于提问
- 如果实在遇到了无法解决的问题，或是Lab的开发因为某个问题已经停滞了超过24h，请使用提问机会以避免在ddl前无法完成该Lab
- 提问前请阅读[How-To-Ask-Questions-The-Smart-Way](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)，不要浪费宝贵的提问机会

## 注意

1. 独立完成该Lab，不要与其他同学沟通任何与系统实现相关的问题
2. 使用Python作为开发语言，具体语言规范可参考[Python语言规范 — Google 开源项目风格指南](https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/python_language_rules.html)
3. 本次Lab不对最终的诊断效果进行任何要求，同学们专注于系统流程的实现即可
4. Lab Pre的时间控制在25-30min之间，实际Pre时会计时，请同学们把握好Pre的时间
5. DeepSeek-V3模型并不是多模态模型，所以本次Lab实现不必考虑语料中的图片
6. 可以使用搜索引擎及任何可以使用的AI工具（包括但不限于GPT、Claude、Grok、Gemini、Kimi等网页AI助手；Cursor、Github Copilot、Claude Code、Gemini CLI等AI编程工具），但请保留使用AI的历史记录，Lab Pre时会进行检查和提问
7. 使用AI编程工具请对AI实现的代码进行充分理解，明白AI为什么会这样进行实现，Lab Pre时会进行检查和提问
8. Lab Pre时除了需要根据`Presentation.ppt/pptx`文件对所实现的系统进行说明外，还需要现场按照`Readme.md`文件将服务启动并进行测试，测试机器会在开学后提供，可供同学们进行部署测试，同时请确保现场演示时服务的可用性
9. 如果在使用docker镜像启动服务时有文件挂载的需求，请在一并将文件打包成的`.zip`压缩包发送到邮箱`zymiao24@m.fudan.edu.cn`；如果docker镜像需要使用GPU，请在发送`.tar`文件时一并告知
10. 受限于CFFF平台账号问题，本次Lab同学们无法使用SAIS计算资源，如果本地计算资源有限或存在环境配置等问题，可使用部署在星河启智平台的`gme-qwen2-vl-7b`Embedding模型，具体使用方法请参考`gme-qwen2-vl-7b使用文档.md`

### Tips

- AI Coding工具的出现极大的加速了此类demo级项目的开发，请同学们大胆使用AI Coding工具，并在Lab开发过程中学习如何使用AI加速选型、开发、测试、部署等各个环节
- 祝同学们好运
