from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from pymongo import MongoClient
import pandas as pd
import sys
import json
import requests

client = MongoClient('mongodb://127.0.0.1:27017')
db = client.FMS
mycol = db['testFiles']
tagCol = db['tags']


def LLMPRE(text_name, text_content, filed, tags):
    prompt_template = PromptTemplate.from_template(
        """
        你是领域专家，按照技术问题（解决什么问题）和技术方案（用什么技术解决问题）提取下列项目的标签
        为下列科技项目书给出关于"{filed}"下的最合适的标签,标签是短语，先给出标签，再和参考列表核对，
        不符和下列科技项目书内容的标签绝对不采用，比如如果文字内容与'人工智能'标签无关，则在输出标签时
        不采用'人工智能'标签，以此类推；标签参考列表为{tags}，标签要精简成高度概括的短语，每个标签都应该给出与文本的相关度，
        相关的为0-1的值，越靠近0越不相关，越靠近1越相关；标签根据内容给出，如果参考标签列表中没有合适的标签则拓展列表，
        标签参考列表可供参考不能完全抄袭可以适当在列表外拓展保证标签合理即可，如果标签之间有包含关系，
        需要给出利用“children”属性给出层次结构，返回格式为JSON形式 
        '''  
        项目标题：{text_name}
        项目内容：{text_content}
        '''
        \输出应只输出格式化为JSON的实例即可,只返回JSON格式,不输出其他任何东西,只输出由大括号包裹的JSON实例,例如
        {outExample}
        """
    )
    print(filed, tags)
    outExamples = {
        "" + str(filed[0]): [{"tagName": "", "relativity": 0.1, "children": []},
                             {"tagName": "", "relativity": 0.8, "children": []}],
        "" + str(filed[1]): [{"tagName": "", "relativity": 0.1, "children": []},
                             {"tagName": "", "relativity": 0.8, "children": []}],
    }
    _input = prompt_template.format(outExample=outExamples, filed=filed, tags=tags, text_name=text_name,
                                    text_content=text_content)
    print(_input)
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key="e8c095a81c1040cf5e6071bc17cd378c.jCPoAEyNw1c3J4zp")  # 填写您自己的APIKey
    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=[
            {"role": "user", "content": _input}
        ],
    )
    print(str(response.choices[0].message.content).replace("```json", "").replace("```", ""))

    # api_url = "https://8g642a1388.goho.co/forward_question/"
    # req_data = {"prompt": _input, "history": []}
    # resp = requests.post(api_url, json=req_data)
    # output = resp.json()['response']  # ['properties']
    # print(output)


def main(FileId):
    #     print('''{
    #   '技术领域': ['算力融合', '集群计算', '异构计算', '高速存储', '无损网络', 'RDMA技术'],
    #   '应用领域': ['超算中心', '智算中心', '企业计算', '科研计算'],
    #   '关键技术': ['算力管理调度', '异构硬件平台', 'GPU自动识别', '算力集群管理平台研发', 'AI计算任务优化', '自主可控技术'],
    #   '研究目标': ['提高效率', '降低成本', '增强安全', '算力集群管理平台研发', '大规模服务器管理', '国产GPU适配', 'AI计算框架兼容', '通信库与操作系统开发'],
    #   '合作模式': ['企业合作', '高校合作', '研究所合作', '政府支持', '国际合作', '技术研发合作', '行业应用合作']
    # }''')
    tagQuery = {"isChoose": True}
    tags = tagCol.find(tagQuery)
    t = {}
    for tag in tags:
        t = tag
    print(t)
    field = t['fields']
    # tagE = []
    # for f in t['tree']['children']:
    #     tmp = []
    #     for tg in f['children']:
    #         tmp.append(tg['name'])
    #     tagE.append(tmp)
    myquery = {"id": FileId}
    doc = mycol.find(myquery)
    for d in doc:
        print(d)
        print(field)
        LLMPRE(d['title'], d['abs'], field, d["keyWordOri"])


if __name__ == '__main__':
    # print(["你好"])
    main("1")
# prompt_template = PromptTemplate.from_template(
#     """
#     为下列科技项目书给出关于"{filed}"下的最合适的标签，标签根据领域内容给出，标签列表可供参考不能完全抄袭，标签列表为{tags}给出的标签一定要贴合文字内容:
#     项目标题：{text_name}
#     项目内容：{text_content}
#     \输出应只输出格式化为JSON的实例即可，例如
#     {outExample}
#     """
# )
# filed = [
#     "技术领域",
#     "应用领域",
#     "关键技术",
#     "研究目标",
#     "合作模式"
# ],
# tt=[]
# tags = [
#     ["人工智能", "云计算", "芯片技术", "生物技术", "环保技术"],
#         ["医疗健康", "教育培训", "工业制造", "数据安全", "能源管理"],
#         ["数据分析", "机器学习", "传感技术", "加密技术", "智能控制"],
#         ["提高效率", "降低成本", "增强安全", "提升用户体验", "促进可持续发展"],
#         ["企业合作", "高校合作", "研究所合作", "政府支持", "国际合作"]
# ]
# outExamples = {
#     ""+str(filed[0][0]): [tags[0][0]]
# }
# text_name = '面向算力融合的集群计算管理关键技术研究和应用'
#
# text_content = '''针对传统超算作业中心与新兴智算作业中心计算任务融
# 合的趋势，研究相应的算力融合管理的架构体系，研制先进的算力集群
# 融合管理平台，提高融合计算场景下异构计算资源的使用效率。研究跨
# 异构硬件平台的算力管理调度技术，实现对包括国产主流 CPU、GPU 等算
# 力资源的统一调度，研究 GPU 计算卡的自动识别和快速适配技术，实现
# 算力资源与管理调度的耦合优化；研究集群算力系统中高速存储、无损
# 网络和高速通信库技术，构建与 RDMA 网络联动和高效交互机制，实现对
# 不同规模集群算力方案的有效支撑和底层核心技术的自主可控；研究 AI
# 计算任务的切分优化和调度优化，提高大模型训练效率；研发先进的融
# 合算力集群管理平台，进行规模应用'''
#
# _input = prompt_template.format(outExample=outExamples, filed=filed, tags=tt, text_name=text_name,
#                                 text_content=text_content)
# from zhipuai import ZhipuAI
# client = ZhipuAI(api_key="e8c095a81c1040cf5e6071bc17cd378c.jCPoAEyNw1c3J4zp") # 填写您自己的APIKey
# response = client.chat.completions.create(
#     model="glm-4",  # 填写需要调用的模型名称
#     messages=[
#         {"role": "user", "content": _input}
#     ],
# )
#
