
HELP_CFG = {
    "title": "三角洲行动 帮助",
    "subTitle": "DeltaForce-Plugin HELP",
    "themeName": "default",
    "colWidth": 420,
    "colCount": 2,
    "twoColumnLayout": True,
    "bgBlur": True
}

HELP_LIST = {
    "fullWidth": [
        {
            "order": 1,
            "group": "所有命令统一使用 /三角洲 前缀，例如 /三角洲 帮助"
        },
        {
            "order": 2,
            "group": "此为基础菜单，其他功能请使用 /三角洲 娱乐帮助 查看娱乐菜单"
        },
        {
            "order": 100,
            "group": "系统管理（仅主人）",
            "masterOnly": True,
            "list": [
                {"icon": 61, "title": "/三角洲 广播开启 | 广播关闭", "desc": "开启/关闭广播通知接收"},
                {"icon": 78, "title": "/三角洲 广播状态", "desc": "查看广播通知设置状态"},
                {"icon": 85, "title": "/三角洲 用户统计", "desc": "查看用户统计数据"},
                {"icon": 64, "title": "/三角洲 ws连接 | ws断开", "desc": "手动连接/断开WebSocket"},
                {"icon": 78, "title": "/三角洲 ws状态", "desc": "查看WebSocket连接状态"},
                {"icon": 92, "title": "/三角洲 更新日志", "desc": "查看更新日志"},
                {"icon": 92, "title": "/三角洲 服务器状态", "desc": "服务器状态"},
                {"icon": 92, "title": "/三角洲 (强制)更新", "desc": "更新三角洲插件"}
            ]
        }
    ],
    "left": [
        {
            "order": 1,
            "group": "账号相关",
            "list": [
                {"icon": 80, "title": "/三角洲 账号", "desc": "查看已绑定token列表"},
                {"icon": 71, "title": "/三角洲 账号切换 [序号]", "desc": "激活指定序号账号"},
                {"icon": 86, "title": "/三角洲 绑定 [token]", "desc": "绑定token"},
                {"icon": 48, "title": "/三角洲 解绑 [序号]", "desc": "解绑指定序号token"},
                {"icon": 47, "title": "/三角洲 删除 [序号]", "desc": "删除QQ/微信登录数据"},
                {"icon": 49, "title": "/三角洲 (微信/QQ)刷新", "desc": "刷新微信/QQ token"},
                {"icon": 64, "title": "/三角洲 (QQ/微信)登陆", "desc": "通过QQ/微信扫码登录"},
                {"icon": 62, "title": "/三角洲 (WeGame)登陆", "desc": "登录WeGame"},
                {"icon": 61, "title": "/三角洲 安全中心登陆", "desc": "通过安全中心扫码登录"},
                {"icon": 71, "title": "/三角洲 (QQ/微信)授权登陆 [code]", "desc": "通过授权码登录"},
                {"icon": 52, "title": "/三角洲 网页登陆", "desc": "通过网页方式登录"},
                {"icon": 80, "title": "/三角洲 ck登陆 [cookies]", "desc": "通过cookie登录"},
                {"icon": 78, "title": "/三角洲 信息", "desc": "查询个人详细信息"},
                {"icon": 71, "title": "/三角洲 UID", "desc": "查询个人UID"}
            ]
        },
        {
            "order": 2,
            "group": "游戏数据",
            "list": [
                {"icon": 41, "title": "/三角洲 藏品 [类型]", "desc": "查询个人仓库资产"},
                {"icon": 48, "title": "/三角洲 货币", "desc": "查询游戏内货币信息"},
                {"icon": 55, "title": "/三角洲 数据 [模式] [赛季]", "desc": "查询个人统计数据"},
                {"icon": 66, "title": "/三角洲 战绩 [模式] [页码]", "desc": "查询战绩（全面/烽火）"},
                {"icon": 78, "title": "/三角洲 地图统计 [模式]", "desc": "查询地图统计数据"},
                {"icon": 53, "title": "/三角洲 流水 [类型/all]", "desc": "查询交易流水"},
                {"icon": 79, "title": "/三角洲 出红记录 [物品名]", "desc": "查询藏品解锁记录"},
                {"icon": 42, "title": "/三角洲 昨日收益 [模式]", "desc": "查询昨日收益和物资统计"}
            ]
        },
        {
            "order": 3,
            "group": "房间管理",
            "list": [
                {"icon": 28, "title": "/三角洲 房间列表", "desc": "查询房间列表"},
                {"icon": 23, "title": "/三角洲 创建房间", "desc": "创建房间"},
                {"icon": 26, "title": "/三角洲 加入房间 [房间号]", "desc": "加入房间"},
                {"icon": 37, "title": "/三角洲 退出房间 [房间号]", "desc": "退出房间"},
                {"icon": 56, "title": "/三角洲 踢人 [序号]", "desc": "踢出房间成员"},
                {"icon": 64, "title": "/三角洲 房间信息", "desc": "查询当前房间信息"},
                {"icon": 62, "title": "/三角洲 房间地图列表", "desc": "查询房间地图列表"},
                {"icon": 78, "title": "/三角洲 房间标签列表", "desc": "查询房间标签列表"}
            ]
        },
        {
            "order": 4,
            "group": "价格/利润查询",
            "list": [
                {"icon": 61, "title": "/三角洲 价格历史 | 当前价格", "desc": "查询物品历史/当前价格"},
                {"icon": 61, "title": "/三角洲 材料价格 [物品ID]", "desc": "查询制造材料最低价格"},
                {"icon": 61, "title": "/三角洲 利润历史 [ID/场所]", "desc": "查询制造利润历史记录"},
                {"icon": 61, "title": "/三角洲 利润排行", "desc": "查询利润排行榜V1"},
                {"icon": 61, "title": "/三角洲 最高利润", "desc": "查询最高利润排行榜V2"},
                {"icon": 62, "title": "/三角洲 特勤处利润 [类型]", "desc": "查询特勤处四个场所利润"}
            ]
        }
    ],
    "right": [
        {
            "order": 1,
            "group": "战报与推送",
            "list": [
                {"icon": 86, "title": "/三角洲 日报 [模式]", "desc": "查询日报数据"},
                {"icon": 86, "title": "/三角洲 周报 [模式] [日期]", "desc": "查询每周战报"},
                {"icon": 46, "title": "/三角洲 每日密码", "desc": "查询今日密码"},
                {"icon": 86, "title": "/三角洲 开启/关闭日报推送", "desc": "开启/关闭日报推送"},
                {"icon": 37, "title": "/三角洲 开启/关闭周报推送", "desc": "开启/关闭周报推送"},
                {"icon": 86, "title": "/三角洲 开启/关闭每日密码推送", "desc": "开启/关闭每日密码推送"},
                {"icon": 86, "title": "/三角洲 开启/关闭特勤处推送", "desc": "开启/关闭特勤处制造完成推送"},
                {"icon": 86, "title": "/三角洲 订阅 战绩 [模式]", "desc": "订阅战绩"},
                {"icon": 80, "title": "/三角洲 取消订阅 战绩", "desc": "取消战绩订阅"},
                {"icon": 78, "title": "/三角洲 订阅状态 战绩", "desc": "查看订阅和推送状态"},
                {"icon": 61, "title": "/三角洲 开启私信订阅推送", "desc": "开启私信推送"},
                {"icon": 61, "title": "/三角洲 开启本群订阅推送", "desc": "开启本群推送"},
                {"icon": 79, "title": "筛选条件", "desc": "百万撤离/百万战损/天才少年"}
            ]
        },
        {
            "order": 2,
            "group": "社区改枪码",
            "list": [
                {"icon": 86, "title": "/三角洲 改枪码上传", "desc": "上传改枪方案"},
                {"icon": 86, "title": "/三角洲 改枪码列表 [武器名]", "desc": "查询改枪方案列表"},
                {"icon": 86, "title": "/三角洲 改枪码详情 [方案ID]", "desc": "查询改枪方案详情"},
                {"icon": 86, "title": "/三角洲 改枪码点赞", "desc": "点赞/点踩改枪方案"},
                {"icon": 86, "title": "/三角洲 改枪码收藏", "desc": "收藏/取消收藏改枪方案"},
                {"icon": 86, "title": "/三角洲 改枪码收藏列表", "desc": "查看已收藏的改枪方案"},
                {"icon": 86, "title": "/三角洲 改枪码更新", "desc": "更新/删除已上传的改枪方案"},
                {"icon": 78, "title": "网站上传修改", "desc": "https://df.shallow.ink/"}
            ]
        },
        {
            "order": 3,
            "group": "实用工具",
            "list": [
                {"icon": 61, "title": "/三角洲 ai锐评 [模式]", "desc": "AI锐评战绩"},
                {"icon": 61, "title": "/三角洲 ai评价 [模式]", "desc": "AI评价战绩(可选预设)"},
                {"icon": 78, "title": "/三角洲 ai预设列表", "desc": "查看AI评价预设"},
                {"icon": 41, "title": "/三角洲 违规记录", "desc": "查询历史违规(需安全中心)"},
                {"icon": 48, "title": "/三角洲 特勤处状态", "desc": "查询特勤处制造状态"},
                {"icon": 71, "title": "/三角洲 特勤处信息 [场所]", "desc": "查询特勤处设施升级信息"},
                {"icon": 71, "title": "/三角洲 物品列表", "desc": "获取物品列表"},
                {"icon": 86, "title": "/三角洲 物品搜索 [名称/ID]", "desc": "搜索游戏内物品"},
                {"icon": 48, "title": "/三角洲 大红收藏 [赛季]", "desc": "生成大红收集海报"},
                {"icon": 40, "title": "/三角洲 文章列表 | 文章详情", "desc": "查看文章列表/详情"},
                {"icon": 71, "title": "/三角洲 健康状态", "desc": "查询游戏健康状态信息"},
                {"icon": 78, "title": "/三角洲 干员 [名称]", "desc": "查询干员详细信息"},
                {"icon": 78, "title": "/三角洲 干员列表", "desc": "查询所有干员列表"}
            ]
        },
        {
            "order": 4,
            "group": "计算工具",
            "list": [
                {"icon": 61, "title": "/三角洲 伤害计算 | 伤害", "desc": "伤害计算"},
                {"icon": 33, "title": "/三角洲 战备计算", "desc": "计算最低成本卡战备配装"}
            ]
        }
    ]
}
