import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
# import asyncio # No longer needed for sync version

# --- 配置 ---
# 使用绝对路径，基于脚本位置
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
# 图片资源目录
PIC_SRC_DIR = PROJECT_ROOT / 'storage' / 'pic_src'

# 简单的翻译和映射
LOCATIONS = {
    "International": "全球",
    "Afghanistan": "阿富汗",
    "Algeria": "阿尔及利亚",
    "Argentina": "阿根廷",
    "Australia": "澳大利亚",
    "Austria": "奥地利",
    "Bangladesh": "孟加拉国",
    "Belgium": "比利时",
    "Brazil": "巴西",
    "Canada": "加拿大",
    "Chile": "智利",
    "China": "中国",
    "Colombia": "哥伦比亚",
    "Cuba": "古巴",
    "Denmark": "丹麦",
    "Egypt": "埃及",
    "Finland": "芬兰",
    "France": "法国",
    "Germany": "德国",
    "Greece": "希腊",
    "Hong Kong": "香港",
    "India": "印度",
    "Indonesia": "印度尼西亚",
    "Iran": "伊朗",
    "Iraq": "伊拉克",
    "Ireland": "爱尔兰",
    "Israel": "以色列",
    "Italy": "意大利",
    "Japan": "日本",
    "Kenya": "肯尼亚",
    "Malaysia": "马来西亚",
    "Mexico": "墨西哥",
    "Netherlands": "荷兰",
    "New Zealand": "新西兰",
    "Nigeria": "尼日利亚",
    "North Korea": "朝鲜",
    "Norway": "挪威",
    "Pakistan": "巴基斯坦",
    "Peru": "秘鲁",
    "Philippines": "菲律宾",
    "Poland": "波兰",
    "Portugal": "葡萄牙",
    "Russia": "俄罗斯",
    "Saudi Arabia": "沙特阿拉伯",
    "Singapore": "新加坡",
    "South Africa": "南非",
    "South Korea": "韩国",
    "Spain": "西班牙",
    "Sweden": "瑞典",
    "Switzerland": "瑞士",
    "Thailand": "泰国",
    "Taiwan": "台湾",
    "Turkey": "土耳其",
    "Ukraine": "乌克兰",
    "United Kingdom": "英国",
    "United States": "美国",
    "Vietnam": "越南"
}
LEAGUES = {
    "Unranked": "未排名",
    #传奇联赛
    "Legend League": "传奇",

    #泰坦联赛
    "Titan League I": "泰坦一",
    "Titan League II": "泰坦二",
    "Titan League III": "泰坦三",

    # 冠军联赛
    "Champion League I": "冠军一",
    "Champion League II": "冠军二",
    "Champion League III": "冠军三",
    
    # 大师联赛
    "Master League I": "大师一",
    "Master League II": "大师二",
    "Master League III": "大师三",
    
    # 水晶联赛
    "Crystal League I": "水晶一",
    "Crystal League II": "水晶二",
    "Crystal League III": "水晶三",
    
    # 黄金联赛
    "Gold League I": "黄金一",
    "Gold League II": "黄金二",
    "Gold League III": "黄金三",
    
    # 白银联赛
    "Silver League I": "白银一",
    "Silver League II": "白银二",
    "Silver League III": "白银三",
    
    # 青铜联赛
    "Bronze League I": "青铜一",
    "Bronze League II": "青铜二",
    "Bronze League III": "青铜三"
}

ROLES = {"leader": "首领", "coLeader": "副首", "admin": "长老", "member": "成员"}
TYPES = {"inviteOnly": "仅限邀请", "anyoneCanJoin": "任何人", "closed": "不可加入"}
FREQUENCIES = {"always": "总是", "twice a week": "每周两次", "once a week": "每周一次", "rarely": "很少", "never": "从不", "unknown": "未设置"}

# --- 辅助函数 ---
def get_value(data, keys, default='N/A'):
    """安全地从嵌套字典中获取值"""
    try:
        for key in keys.split('.'):
            if isinstance(data, list) and key.isdigit():
                data = data[int(key)]
            elif isinstance(data, dict):
                 data = data[key]
            else:
                return default
        return data if data is not None else default
    except (KeyError, IndexError, TypeError):
        return default

def translate_role(role):
    return ROLES.get(role, role)

def translate_type(clan_type):
    return TYPES.get(clan_type, clan_type)

def translate_league(league):
    return LEAGUES.get(league, league)

def translate_frequency(frequency):
    return FREQUENCIES.get(frequency, frequency)

def format_bool(value, true_text="是", false_text="否"):
    return true_text if value else false_text

def format_location(location_data):
    name = get_value(location_data, 'name', '')
    is_country = get_value(location_data, 'isCountry', False)
    if is_country:
        return LOCATIONS.get(name, name)
    return name

def get_resource_path(filename):
    """获取资源文件的绝对路径"""
    resource_path = PIC_SRC_DIR / filename
    if not resource_path.exists():
        print(f"警告: 资源文件不存在 - {resource_path}")
        # 如果找不到文件，可以返回一个默认图片路径
        return f"file://{PIC_SRC_DIR}/default.png"
    return f"file://{resource_path.absolute()}"

def get_role_class(role):
    """获取角色对应的CSS类名"""
    role_lower = role.lower() if role else ""
    if "leader" == role_lower:
        return "leader"
    elif "coleader" == role_lower or "co-leader" == role_lower or "副首" == role_lower:
        return "coLeader"
    elif "admin" == role_lower or "elder" == role_lower or "长老" == role_lower:
        return "admin"
    return ""

# --- HTML 生成 ---
def generate_html(data):
    """根据部落数据生成 HTML 字符串"""
    clan_name = get_value(data, 'name')
    clan_tag = get_value(data, 'tag')
    clan_badge_url = get_value(data, 'badgeUrls.large')
    clan_labels = get_value(data, 'labels', [])
    clan_members_count = get_value(data, 'members')
    clan_league = translate_league(get_value(data, 'warLeague.name'))
    clan_location = format_location(get_value(data, 'location', "未设置"))
    clan_language = get_value(data, 'chatLanguage.name', "未设置")
    clan_frequency = translate_frequency(get_value(data, 'warFrequency'))
    clan_log_public = format_bool(get_value(data, 'isWarLogPublic'), "公开", "不公开")
    clan_win_streak = get_value(data, 'warWinStreak')
    clan_wins = get_value(data, 'warWins')
    clan_ties = get_value(data, 'warTies')
    clan_losses = get_value(data, 'warLosses')
    clan_type = translate_type(get_value(data, 'type'))
    clan_req_th = get_value(data, 'requiredTownhallLevel', '无')
    clan_req_trophies = get_value(data, 'requiredTrophies', '无')
    clan_req_builder_trophies = get_value(data, 'requiredBuilderBaseTrophies', '无')
    clan_family_friendly = format_bool(get_value(data, 'isFamilyFriendly'))
    clan_description = get_value(data, 'description', '').replace('\n', '<br>') # 替换换行符
    member_list = get_value(data, 'memberList', [])
    
    # 奖杯数据
    clan_points = get_value(data, 'clanPoints', 0)
    clan_builder_points = get_value(data, 'clanBuilderBasePoints', 0)
    clan_capital_points = get_value(data, 'clanCapitalPoints', 0)

    # --- CSS 样式 ---
    css = """
    body {
        font-family: 'HarmonyOS Sans SC', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f0f2f5;
        color: #333;
        margin: 0;
        padding: 0;
        width: 100%;
        box-sizing: border-box;
    }
    .container {
        background-color: #fff;
        width: 100%;
        max-width: 740px;
        margin: 0 auto;
        padding: 15px 15px 10px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .clan-header {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        background: linear-gradient(to bottom, #fafafa, #f5f5f5);
        border-radius: 8px;
        padding: 16px 15px 14px;
        border: 1px solid #eaeaea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .left-section {
        width: 45%;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    .basic-info {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        width: 100%;
    }
    .badge-container {
        flex-shrink: 0;
        position: relative;
    }
    .badge-container img.badge {
        width: 105px;
        height: 105px;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        border: 3px solid rgba(255, 193, 7, 0.2);
        background: radial-gradient(circle at center, rgba(255,255,255,0.8), rgba(255,255,255,0));
    }
    .badge-container::after {
        content: '';
        position: absolute;
        top: -5px;
        left: -5px;
        right: -5px;
        bottom: -5px;
        background: radial-gradient(circle at center, rgba(255, 215, 0, 0.15), transparent 70%);
        z-index: -1;
        border-radius: 50%;
    }
    .clan-title {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding-left: 5px;
        min-width: 0; /* 确保弹性子项可以缩小到小于内容宽度 */
        overflow: hidden; /* 防止溢出 */
    }
    .clan-title h1 {
        margin: 0 0 2px 0;
        font-size: 20px;
        color: #2d2d2d;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
        letter-spacing: -0.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .name-tag-container {
        display: flex;
        flex-direction: column;
        margin-bottom: 5px;
        max-width: 100%;
    }
    .clan-name-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 5px;
        width: 100%;
        overflow: hidden; /* 防止内容溢出 */
    }
    .family-friendly-icon {
        width: 24px;
        height: 24px;
        margin-left: 0;
        flex-shrink: 0; /* 防止图标缩小 */
    }
    .clan-title .tag {
        font-size: 18px;
        color: #606770;
        margin-top: 3px;
    }
    .labels {
        display: flex;
        flex-wrap: wrap;
        margin-top: 6px;
    }
    .labels img {
        height: 36px;
        margin-right: 8px;
        margin-bottom: 5px;
        vertical-align: middle;
        filter: drop-shadow(0 1px 2px rgba(0,0,0,0.15));
        transition: transform 0.2s ease;
    }
    .labels img:hover {
        transform: scale(1.1);
    }
    .trophy-showcase {
        display: flex;
        justify-content: space-around;
        padding: 8px 8px;
        margin: 10px 0;
        background: linear-gradient(to right, rgba(255, 215, 0, 0.05), rgba(255, 193, 7, 0.1), rgba(255, 215, 0, 0.05));
        border-radius: 8px;
        border: 1px solid rgba(255, 193, 7, 0.2);
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .trophy-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 12px;
        position: relative;
    }
    .trophy-item::after {
        content: '';
        position: absolute;
        top: 50%;
        right: 0;
        height: 60%;
        width: 1px;
        background: linear-gradient(to bottom, transparent, rgba(212, 175, 55, 0.2), transparent);
        transform: translateY(-50%);
    }
    .trophy-item:last-child::after {
        display: none;
    }
    .trophy-icon {
        width: 32px;
        height: 32px;
        object-fit: contain;
        margin-bottom: 6px;
        filter: drop-shadow(0 2px 2px rgba(0,0,0,0.12));
    }
    .trophy-count {
        font-weight: bold;
        color: #b8860b;
        text-shadow: 0 1px 1px rgba(255,255,255,0.8);
        font-size: 18px;
    }
    .trophy-label {
        font-size: 12px;
        color: #666;
        margin-top: 3px;
        font-weight: 500;
    }
    .clan-description {
        background-color: rgba(253, 245, 230, 0.6);
        border-left: 4px solid #ffc107;
        border-radius: 8px;
        padding: 15px 16px;
        font-size: 16px;
        line-height: 1.6;
        flex-grow: 1;
        overflow-y: auto;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        position: relative;
        margin-top: 12px;
        border: 1px solid rgba(255, 193, 7, 0.2);
        background-image: linear-gradient(to bottom, rgba(255, 248, 225, 0.4) 0%, rgba(255, 248, 225, 0.1) 100%);
    }
    .clan-description::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #ffc107, transparent);
        border-radius: 8px 8px 0 0;
    }
    .clan-description::after {
        content: '';
        position: absolute;
        bottom: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cpath fill='%23ffc107' fill-opacity='0.05' d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z'/%3E%3C/svg%3E");
        opacity: 0.3;
        pointer-events: none;
    }
    .clan-description strong {
        display: block;
        margin-bottom: 10px;
        font-size: 20px;
        color: #e67e22;
        border-bottom: 1px dashed rgba(230, 126, 34, 0.3);
        padding-bottom: 8px;
        letter-spacing: 0.5px;
        text-shadow: 0 1px 1px rgba(255,255,255,0.8);
        position: relative;
        padding-left: 26px;
    }
    .clan-description strong::before {
        content: '📝';
        position: absolute;
        left: 0;
        top: 0;
        font-size: 18px;
    }
    .clan-description p {
        margin: 8px 0;
    }
    .right-section {
        width: 55%;
        display: flex;
        flex-direction: column;
    }
    .info-section {
        margin-bottom: 12px;
        background-color: #fff;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .info-section:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(0,0,0,0.08);
    }
    .info-section:last-child {
        margin-bottom: 0;
    }
    /* 基本信息主题 */
    .info-section:nth-child(1) {
        border-top: 3px solid #4caf50;
    }
    .info-section:nth-child(1) .section-title::before {
        background-color: #4caf50;
    }
    .info-section:nth-child(1) .section-title::after {
        background-color: #4caf50;
    }
    .info-section:nth-child(1)::after {
        content: '';
        position: absolute;
        top: -15px;
        right: -15px;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0) 70%);
        border-radius: 50%;
        z-index: 0;
    }
    /* 对战信息主题 */
    .info-section:nth-child(2) {
        border-top: 3px solid #ff5722;
    }
    .info-section:nth-child(2) .section-title::before {
        background-color: #ff5722;
    }
    .info-section:nth-child(2) .section-title::after {
        background-color: #ff5722;
    }
    .info-section:nth-child(2)::after {
        content: '';
        position: absolute;
        top: -15px;
        right: -15px;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(255, 87, 34, 0.1) 0%, rgba(255, 87, 34, 0) 70%);
        border-radius: 50%;
        z-index: 0;
    }
    /* 加入要求主题 */
    .info-section:nth-child(3) {
        border-top: 3px solid #2196f3;
    }
    .info-section:nth-child(3) .section-title::before {
        background-color: #2196f3;
    }
    .info-section:nth-child(3) .section-title::after {
        background-color: #2196f3;
    }
    .info-section:nth-child(3)::after {
        content: '';
        position: absolute;
        top: -15px;
        right: -15px;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0) 70%);
        border-radius: 50%;
        z-index: 0;
    }
    .section-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #333;
        padding-bottom: 6px;
        border-bottom: 1px solid #f0f0f0;
        position: relative;
        display: flex;
        align-items: center;
        z-index: 1;
    }
    .section-title::before {
        content: '';
        display: inline-block;
        width: 5px;
        height: 18px;
        background-color: #ffc107;
        margin-right: 10px;
        border-radius: 2px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .section-title::after {
        content: '';
        position: absolute;
        left: 0;
        bottom: -1px;
        width: 60px;
        height: 2px;
        background-color: #ffc107;
        border-radius: 1px;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        font-size: 13px;
        position: relative;
        z-index: 1;
    }
    .info-item {
        background-color: #f9f9f9;
        padding: 10px 12px;
        border-radius: 8px;
        border: 1px solid #f0f0f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .info-item:hover {
        background-color: #f5f9ff;
        border-color: #e3ecfa;
        transform: translateY(-2px);
        box-shadow: 0 3px 6px rgba(0,0,0,0.06);
    }
    .info-item-label {
        color: #555;
        font-weight: 600;
    }
    .info-item-value {
        text-align: right;
        color: #333;
        font-weight: 500;
    }
    .members-section h2 {
        font-size: 16px;
        color: #333;
        border-bottom: 1px solid #eaeaea;
        padding: 8px 12px;
        margin: 10px 0 8px 0;
        position: relative;
        background: linear-gradient(to right, rgba(255, 193, 7, 0.05), transparent);
        border-radius: 8px 8px 0 0;
        text-shadow: 0 1px 1px rgba(255,255,255,0.8);
        display: flex;
        align-items: center;
    }
    .members-section h2::before {
        content: '';
        display: inline-block;
        width: 5px;
        height: 18px;
        background-color: #ffc107;
        margin-right: 10px;
        border-radius: 2px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .members-section h2::after {
        content: '';
        position: absolute;
        left: 0;
        bottom: -1px;
        width: 100px;
        height: 2px;
        background: linear-gradient(to right, #ffc107, transparent);
        border-radius: 2px;
    }
    .member-list {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        margin-top: 6px;
    }
    .thumbnail-container {
        width: 100%;
        height: auto;
        overflow: hidden;
        border-radius: 4px;
    }
    .thumbnail-container img {
        width: 100%;
        height: auto;
        object-fit: cover;
    }
    .member-card {
        background-color: #fff;
        border: 1px solid #eaeaea;
        border-radius: 6px;
        padding: 8px;
        font-size: 12px;
        line-height: 1.2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: all 0.25s ease;
    }
    .member-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        border-color: #ffc107;
    }
    /* 特殊排名成员卡片样式 */
    .member-card:nth-child(1) {
        background: linear-gradient(to bottom right, rgba(255, 215, 0, 0.05), rgba(255, 215, 0, 0.02));
        border-color: rgba(255, 215, 0, 0.3);
    }
    .member-card:nth-child(2) {
        background: linear-gradient(to bottom right, rgba(192, 192, 192, 0.15), rgba(220, 220, 220, 0.25));
        border-color: rgba(192, 192, 192, 0.5);
        box-shadow: 0 2px 8px rgba(192, 192, 192, 0.3);
        position: relative;
    }
    .member-card:nth-child(2)::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 100%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.5), transparent);
        z-index: 0;
        pointer-events: none;
    }
    /* 移除了会导致错位的通配符选择器 */
    .member-card:nth-child(2) .member-header,
    .member-card:nth-child(2) .details,
    .member-card:nth-child(2) .member-info-container,
    .member-card:nth-child(2) .left-details,
    .member-card:nth-child(2) .right-details {
        position: relative;
        z-index: 1;
    }
    .member-card:nth-child(3) {
        background: linear-gradient(to bottom right, rgba(205, 127, 50, 0.05), rgba(205, 127, 50, 0.02));
        border-color: rgba(205, 127, 50, 0.3);
    }
    /* 角色样式 - 移除了边框颜色突出 */
    .member-card.member {
        background-color: #78909c;
        box-shadow: 0 1px 2px rgba(120, 144, 156, 0.2);
    }
    .member-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        padding-bottom: 3px;
        border-bottom: 1px solid #f5f5f5;
    }
    .member-info-container {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 1;
        min-width: 0; /* 防止子元素撑破容器 */
    }
    .member-name {
        font-weight: 600;
        font-size: 11px;
        color: #1c1e21;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
        min-width: 0; /* 确保文本截断正常工作 */
        max-width: 100px; /* 限制最大宽度 */
    }
    /* 没有职位标签时的样式 */
    .member-header:not(:has(.role)) .member-name {
        max-width: 120px; /* 没有职位标签时的最大宽度 */
    }
    /* 有职位标签时的样式 */
    .member-header:has(.role) .member-name {
        max-width: 100px; /* 有职位标签时的最大宽度 */
    }
    .rank-display {
        min-width: 16px;
        height: 16px;
        background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 9px;
        color: #555;
        margin-right: 2px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        position: relative;
        overflow: hidden;
    }
    .rank-display::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 50%;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 4px 4px 0 0;
    }
    
    /* 特殊排名样式 */
    .member-card:nth-child(-n+3) .rank-display {
        color: #fff;
        font-weight: 700;
    }
    .member-card:nth-child(1) .rank-display {
        background: linear-gradient(135deg, #ffd700, #ffa500);
        box-shadow: 0 1px 3px rgba(255, 165, 0, 0.4);
    }
    .member-card:nth-child(2) .rank-display {
        background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
        box-shadow: 0 1px 3px rgba(160, 160, 160, 0.6);
        position: relative;
        overflow: hidden;
    }
    .member-card:nth-child(2) .rank-display::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%);
        animation: silverShine 2s infinite;
        pointer-events: none;
    }
    @keyframes silverShine {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }
    .member-card:nth-child(3) .rank-display {
        background: linear-gradient(135deg, #cd7f32, #a05a2c);
        box-shadow: 0 1px 3px rgba(160, 90, 44, 0.4);
    }
    .th_icon {
        width: 14px;
        height: 14px;
        object-fit: contain;
        margin-right: 2px;
    }
    .member-tag {
        font-size: 9px;
        color: #888;
    }
    .member-card .details {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #606770;
        margin-top: 2px;
        min-height: 20px;
    }
    .member-card .left-details {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .member-card .right-details {
        display: flex;
        align-items: center;
    }
    .exp-level {
        display: flex;
        align-items: center;
        position: relative;
        margin-left: 2px;
    }
    .exp-icon {
        width: 15px;
        height: 15px;
    }
    .exp-level-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 7px;
        font-weight: bold;
        color: #000;
        text-shadow: 0px 0px 2px #fff, 0px 0px 2px #fff;
    }
    .member-card .trophies {
        display: flex;
        align-items: center;
    }
    .member-card .trophies img {
        width: 14px;
        height: 14px;
        margin-right: 1px;
    }
    .member-card .role {
        padding: 1px 4px;
        font-size: 8px;
        font-weight: 600;
        border-radius: 2px;
        color: #fff;
        letter-spacing: 0.2px;
        text-transform: uppercase;
        flex-shrink: 0; /* 防止职位标签被压缩 */
        min-width: max-content; /* 确保文本不会被截断 */
    }
    .member-card .role.leader {
        background-color: #ffc107;
        box-shadow: 0 1px 2px rgba(255, 193, 7, 0.2);
    }
    .member-card .role.coLeader {
        background-color: #9c27b0;
        box-shadow: 0 1px 2px rgba(156, 39, 176, 0.2);
    }
    .member-card .role.admin {
        background-color: #2196f3;
        box-shadow: 0 1px 2px rgba(33, 150, 243, 0.2);
    }
    .member-card .role.member {
        background-color: #78909c;
        box-shadow: 0 1px 2px rgba(120, 144, 156, 0.2);
    }
    """

    # --- HTML 结构 ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>部落信息: {clan_name}</title>
        <style>{css}</style>
        <script>
        // 动态调整部落名称的字体大小和徽标
        document.addEventListener('DOMContentLoaded', function() {{
            const clanNameElement = document.querySelector('.clan-title h1');
            const badgeElement = document.querySelector('.badge-container img.badge');
            const clanNameContainer = document.querySelector('.clan-name-container');
            
            if (clanNameElement && badgeElement) {{
                const nameLength = clanNameElement.textContent.length;
                
                // 根据名称长度动态调整
                if (nameLength > 20) {{
                    // 长名称 (20-30 字符)
                    clanNameElement.style.fontSize = '24px';
                }}
                
                if (nameLength > 30) {{
                    // 超长名称 (超过30字符)
                    clanNameElement.style.fontSize = '20px';
                    badgeElement.style.width = '95px';
                    badgeElement.style.height = '95px';
                }}
                
                if (nameLength > 40) {{
                    // 极长名称 (超过40字符)
                    clanNameElement.style.fontSize = '18px';
                    badgeElement.style.width = '90px';
                    badgeElement.style.height = '90px';
                    
                    // 如果文本仍然溢出，添加省略号
                    if (clanNameElement.scrollWidth > clanNameElement.clientWidth) {{
                        const text = clanNameElement.textContent;
                        const maxChars = Math.floor(text.length * (clanNameElement.clientWidth / clanNameElement.scrollWidth)) - 3;
                        clanNameElement.textContent = text.substring(0, maxChars) + '...';
                    }}
                }}
            }}
        }});
        </script>
    </head>
    <body>
        <div class="container">
            <div class="clan-header">
                <div class="left-section">
                    <div class="basic-info">
                        <div class="badge-container">
                            <img src="{clan_badge_url}" alt="部落徽章" class="badge">
                        </div>
                        <div class="clan-title">
                            <div class="name-tag-container">
                                <div class="clan-name-container">
                                    <h1>{clan_name}</h1>
                                    <img 
                                        src="{get_resource_path('clan/family_friendly_' + ('yes' if clan_family_friendly == '是' else 'no') + '.png')}" 
                                        alt="{'全年龄' if clan_family_friendly == '是' else '非全年龄'}" 
                                        title="{'全年龄' if clan_family_friendly == '是' else '非全年龄'}"
                                        class="family-friendly-icon">
                                </div>
                                <span class="tag">{clan_tag}</span>
                                
                            </div>
                            <div class="labels">
                                {''.join([f'<img src="{get_value(label, "iconUrls.small")}" alt="{get_value(label, "name")}">' for label in clan_labels])}
                            </div>
                        </div>
                    </div>
                    
                    <div class="trophy-showcase">
                        <div class="trophy-item">
                            <img src="{get_resource_path('clan/clan_points.png')}" alt="主世界奖杯" class="trophy-icon">
                            <span class="trophy-count">{clan_points}</span>
                        </div>
                        <div class="trophy-item">
                            <img src="{get_resource_path('clan/builder_points.png')}" alt="夜世界奖杯" class="trophy-icon">
                            <span class="trophy-count">{clan_builder_points}</span>
                        </div>
                        <div class="trophy-item">
                            <img src="{get_resource_path('clan/capital_points.png')}" alt="部落首都" class="trophy-icon">
                            <span class="trophy-count">{clan_capital_points}</span>
                        </div>
                    </div>
                    
                    <div class="clan-description">
                        <strong>描述</strong>
                        {clan_description if clan_description else '无'}
                    </div>
                </div>
                <div class="right-section">
                    <div class="info-section">
                        <div class="section-title">
                            <span style="display: inline-flex; align-items: center; margin-right: 6px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                </svg>
                            </span>
                            基本信息
                        </div>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-item-label">位置:</span>
                                <span class="info-item-value">{clan_location}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">语言:</span>
                                <span class="info-item-value">{clan_language}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">联赛:</span>
                                <span class="info-item-value">{clan_league}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">人数:</span>
                                <span class="info-item-value">{clan_members_count}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <div class="section-title">
                            <span style="display: inline-flex; align-items: center; margin-right: 6px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff5722" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                                </svg>
                            </span>
                            对战信息
                        </div>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-item-label">频率:</span>
                                <span class="info-item-value">{clan_frequency}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">日志:</span>
                                <span class="info-item-value">{clan_log_public}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">连胜:</span>
                                <span class="info-item-value">{clan_win_streak}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">战绩:</span>
                                <span class="info-item-value">{clan_wins}胜/{clan_ties}平/{clan_losses}负</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <div class="section-title">
                            <span style="display: inline-flex; align-items: center; margin-right: 6px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2196f3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="8.5" cy="7" r="4"></circle>
                                    <line x1="20" y1="8" x2="20" y2="14"></line>
                                    <line x1="23" y1="11" x2="17" y2="11"></line>
                                </svg>
                            </span>
                            加入要求
                        </div>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-item-label">方式:</span>
                                <span class="info-item-value">{clan_type}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">大本要求:</span>
                                <span class="info-item-value">{clan_req_th}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">主世界杯数:</span>
                                <span class="info-item-value">{clan_req_trophies}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item-label">夜世界杯数:</span>
                                <span class="info-item-value">{clan_req_builder_trophies}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="members-section">
                <h2>成员列表</h2>
                <div class="member-list">
    """

    # 添加成员列表
    for member in sorted(member_list, key=lambda m: get_value(m, 'clanRank', 99)): # 按排名排序
        rank = get_value(member, 'clanRank')
        name = get_value(member, 'name')
        tag = get_value(member, 'tag')
        exp_level = get_value(member, 'expLevel')
        th_level = get_value(member, 'townHallLevel')
        trophies = get_value(member, 'trophies')
        league_icon = get_value(member, 'league.iconUrls.tiny', '') # 使用 tiny 图标
        role = get_value(member, 'role', '')
        role_display = translate_role(role)
        
        # 获取角色对应的CSS类
        role_class = get_role_class(role)

        html_content += f"""
                    <div class="member-card {role_class}">
                        <div class="member-header">
                            <div class="member-info-container">
                                <div class="rank-display">{rank}</div>
                                <img class="th_icon" src = "{get_resource_path('member/' + str(th_level) + '.png')}">
                                <div class="member-name">{name}</div>
                            </div>
                            {f'<span class="role {role_class}">{role_display}</span>' if role.lower() != "member" else ''}
                        </div>
                        <div class="details">
                            <div class="left-details">
                                <div class="exp-level">
                                    <img class="exp-icon" src="{get_resource_path('member/exp.png')}">
                                    <span class="exp-level-text">{exp_level}</span>
                                </div>
                                <div class="member-tag">{tag}</div>
                            </div>
                            <div class="right-details">
                                <span class="trophies">
                                    {f'<img src="{league_icon}" alt="奖杯图标">' if league_icon else ''}
                                    {trophies}
                                </span>
                            </div>
                        </div>
                    </div>
        """

    html_content += """
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def generate_clan_info_image(data, output_path=None):
    """
    生成部落信息图片
    
    Args:
        data: 部落数据字典
        output_path: 输出图片路径，如果为None则使用默认路径
        
    Returns:
        生成的图片路径
    """
    # 生成HTML内容
    html_content = generate_html(data)
    
    # 创建临时HTML文件
    temp_html_path = Path('temp_clan.html')
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 如果未指定输出路径，使用默认路径
    if output_path is None:
        output_path = Path('clan_info.png')
    
    # 使用Playwright截图
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 740, "height": 600})
        page.goto(f'file://{temp_html_path.absolute()}')
        
        # 等待页面加载完成
        page.wait_for_load_state('networkidle')
        
        # 获取内容区域
        container = page.locator('.container')
        
        # 截取内容区域
        container.screenshot(path=output_path)
        
        browser.close()
    
    # 删除临时HTML文件
    temp_html_path.unlink()
    
    return output_path

# 如果直接运行此脚本，执行示例
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # 从命令行参数中获取JSON文件路径
        json_file = sys.argv[1]
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            output_path = generate_clan_info_image(data)
            print(f"部落信息图片已生成: {output_path}")
        except Exception as e:
            print(f"生成图片时出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("用法: python clan_info.py <json_file>")
