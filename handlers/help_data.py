
HELP_CFG = {
    "title": "三角洲行动 帮助",
    "subTitle": "DeltaForce-Plugin HELP",
    "themeName": "default",
    "colWidth": 420,
    "colCount": 2,
    "twoColumnLayout": True,
    "bgBlur": True,
    "width": 1000
}

HELP_LIST = {
    "fullWidth": [
        {
            "order": 1,
            "group": "所有命令统一使用 /三角洲前缀，例如 /三角洲帮助"
        },
        {
            "order": 100,
            "group": "系统管理（仅主人）",
            "masterOnly": True,
            "list": [
                {"icon": 61, "title": "/三角洲广播开启 | 广播关闭", "desc": "开启/关闭广播通知接收"},
                {"icon": 78, "title": "/三角洲广播状态", "desc": "查看广播通知设置状态"},
                {"icon": 85, "title": "/三角洲用户统计", "desc": "查看用户统计数据"},
                {"icon": 92, "title": "/三角洲更新日志", "desc": "查看更新日志"},
                {"icon": 92, "title": "/三角洲服务器状态", "desc": "服务器状态"},
                {"icon": 92, "title": "/三角洲插件状态", "desc": "查看插件状态"},
            ]
        }
    ],
    "left": [
        {
            "order": 1,
            "group": "账号相关",
            "list": [
                {"icon": 80, "title": "/三角洲账号列表", "desc": "查看已绑定账号"},
                {"icon": 71, "title": "/三角洲切换 [序号]", "desc": "激活指定序号账号"},
                {"icon": 48, "title": "/三角洲解绑 [序号]", "desc": "解绑指定序号token"},
                {"icon": 47, "title": "/三角洲删除 [序号]", "desc": "删除QQ/微信登录数据"},
                {"icon": 49, "title": "/三角洲QQ刷新", "desc": "刷新QQ token"},
                {"icon": 49, "title": "/三角洲微信刷新", "desc": "刷新微信 token"},
                {"icon": 64, "title": "/三角洲QQ登录", "desc": "通过QQ扫码登录"},
                {"icon": 64, "title": "/三角洲微信登录", "desc": "通过微信扫码登录"},
                {"icon": 62, "title": "/三角洲WeGame登录", "desc": "登录WeGame"},
                {"icon": 61, "title": "/三角洲安全中心登录", "desc": "通过安全中心扫码登录"},
                {"icon": 80, "title": "/三角洲CK登录 [cookies]", "desc": "通过cookie登录"},
                {"icon": 78, "title": "/三角洲信息", "desc": "查询个人详细信息"},
                {"icon": 71, "title": "/三角洲UID", "desc": "查询个人UID"}
            ]
        },
        {
            "order": 2,
            "group": "游戏数据",
            "list": [
                {"icon": 41, "title": "/三角洲藏品 [类型]", "desc": "查询个人仓库资产"},
                {"icon": 48, "title": "/三角洲货币", "desc": "查询游戏内货币信息"},
                {"icon": 55, "title": "/三角洲数据 [模式] [赛季]", "desc": "查询个人统计数据"},
                {"icon": 66, "title": "/三角洲战绩 [模式] [页码]", "desc": "查询战绩（全面/烽火）"},
                {"icon": 78, "title": "/三角洲地图统计 [模式]", "desc": "查询地图统计数据"},
                {"icon": 53, "title": "/三角洲流水 [类型/all]", "desc": "查询交易流水"},
                {"icon": 79, "title": "/三角洲出红记录 [物品名]", "desc": "查询藏品解锁记录"},
                {"icon": 42, "title": "/三角洲昨日收益 [模式]", "desc": "查询昨日收益和物资统计"}
            ]
        },
        {
            "order": 3,
            "group": "房间管理",
            "list": [
                {"icon": 28, "title": "/三角洲房间列表", "desc": "查询房间列表"},
                {"icon": 23, "title": "/三角洲创建房间", "desc": "创建房间"},
                {"icon": 26, "title": "/三角洲加入房间 [房间号]", "desc": "加入房间"},
                {"icon": 37, "title": "/三角洲退出房间 [房间号]", "desc": "退出房间"},
                {"icon": 64, "title": "/三角洲房间信息", "desc": "查询当前房间信息"},
                {"icon": 62, "title": "/三角洲房间地图列表", "desc": "查询房间地图列表"},
                {"icon": 78, "title": "/三角洲房间标签", "desc": "查询房间标签列表"}
            ]
        },
        {
            "order": 4,
            "group": "价格/利润查询",
            "list": [
                {"icon": 61, "title": "/三角洲价格 [物品]", "desc": "查询物品价格"},
                {"icon": 61, "title": "/三角洲材料价格 [物品ID]", "desc": "查询制造材料最低价格"},
                {"icon": 61, "title": "/三角洲利润排行", "desc": "查询利润排行榜V1"},
                {"icon": 61, "title": "/三角洲最高利润", "desc": "查询最高利润排行榜V2"},
                {"icon": 62, "title": "/三角洲特勤处利润 [类型]", "desc": "查询特勤处四个场所利润"}
            ]
        }
    ],
    "right": [
        {
            "order": 1,
            "group": "战报与推送",
            "list": [
                {"icon": 86, "title": "/三角洲日报 [模式]", "desc": "查询日报数据"},
                {"icon": 86, "title": "/三角洲周报 [模式] [日期]", "desc": "查询每周战报"},
                {"icon": 46, "title": "/三角洲每日密码", "desc": "查询今日密码"},
                {"icon": 86, "title": "/三角洲订阅战绩 [模式]", "desc": "订阅战绩"},
                {"icon": 80, "title": "/三角洲取消订阅", "desc": "取消战绩订阅"},
                {"icon": 78, "title": "/三角洲订阅状态", "desc": "查看订阅和推送状态"},
                {"icon": 79, "title": "筛选条件", "desc": "百万撤离/百万战损/天才少年"}
            ]
        },
        {
            "order": 2,
            "group": "社区改枪码",
            "list": [
                {"icon": 86, "title": "/三角洲改枪码上传", "desc": "上传改枪方案"},
                {"icon": 86, "title": "/三角洲改枪码列表 [武器名]", "desc": "查询改枪方案列表"},
                {"icon": 86, "title": "/三角洲改枪码详情 [方案ID]", "desc": "查询改枪方案详情"},
                {"icon": 86, "title": "/三角洲改枪码点赞", "desc": "点赞/点踩改枪方案"},
                {"icon": 86, "title": "/三角洲改枪码收藏", "desc": "收藏/取消收藏改枪方案"},
                {"icon": 86, "title": "/三角洲改枪码收藏列表", "desc": "查看已收藏的改枪方案"},
                {"icon": 86, "title": "/三角洲改枪码更新", "desc": "更新/删除已上传的改枪方案"},
            ]
        },
        {
            "order": 3,
            "group": "实用工具",
            "list": [
                {"icon": 61, "title": "/三角洲ai锐评 [模式]", "desc": "AI锐评战绩"},
                {"icon": 61, "title": "/三角洲ai评价 [模式]", "desc": "AI评价战绩(可选预设)"},
                {"icon": 78, "title": "/三角洲ai预设列表", "desc": "查看AI评价预设"},
                {"icon": 41, "title": "/三角洲违规历史", "desc": "查询历史违规(需安全中心)"},
                {"icon": 48, "title": "/三角洲特勤处状态", "desc": "查询特勤处制造状态"},
                {"icon": 71, "title": "/三角洲特勤处信息 [场所]", "desc": "查询特勤处设施升级信息"},
                {"icon": 71, "title": "/三角洲物品列表", "desc": "获取物品列表"},
                {"icon": 86, "title": "/三角洲搜索 [名称/ID]", "desc": "搜索游戏内物品"},
                {"icon": 48, "title": "/三角洲大红收藏 [赛季]", "desc": "生成大红收集海报"},
                {"icon": 40, "title": "/三角洲文章列表", "desc": "查看文章列表"},
                {"icon": 40, "title": "/三角洲文章详情 [ID]", "desc": "查看文章详情"},
                {"icon": 71, "title": "/三角洲健康状态", "desc": "查询游戏健康状态信息"},
                {"icon": 78, "title": "/三角洲干员 [名称]", "desc": "查询干员详细信息"},
                {"icon": 78, "title": "/三角洲干员列表", "desc": "查询所有干员列表"},
                {"icon": 78, "title": "/三角洲TTS状态", "desc": "查询TTS服务状态"},
                {"icon": 78, "title": "/三角洲TTS角色列表", "desc": "获取TTS角色预设列表"},
                {"icon": 78, "title": "/三角洲TTS角色详情", "desc": "获取TTS角色预设详情"},
                {"icon": 78, "title": "/三角洲TTS", "desc": "TTS语音合成"},
                {"icon": 78, "title": "/三角洲鼠鼠音乐", "desc": "播放鼠鼠音乐"},
                {"icon": 78, "title": "/三角洲音乐列表", "desc": "获取音乐列表"},
                {"icon": 78, "title": "/三角洲鼠鼠歌单", "desc": "获取鼠鼠歌单"}
            ]
        }
    ]
}
