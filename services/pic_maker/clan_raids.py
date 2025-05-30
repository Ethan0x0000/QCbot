import json
import os
import base64 # 添加 base64 模块
from playwright.sync_api import sync_playwright
from pathlib import Path # Import Path

# --- 配置 ---
JSON_FILE_PATH = os.path.join('capital.json')
OUTPUT_IMAGE_PATH = 'raid_attack_list.png'
# MAX_MEMBERS_TO_SHOW = 50 # Removed limit

# --- 图片路径配置 (参考 clan_info.py) ---
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
# 指向包含所需图标的目录
PIC_SRC_DIR = PROJECT_ROOT / 'storage' / 'pic_src'

# 定义固定的图片路径
BONUS_RAID_IMG_PATH = PIC_SRC_DIR / 'member' / 'Bonus Raid.png'
NOBONUS_RAID_IMG_PATH = PIC_SRC_DIR / 'member' / 'Nobonus Raid.png'
CAPITAL_RESOURCE_IMG_PATH = PIC_SRC_DIR / 'member' / 'Capital Resource.png'

# --- 辅助函数 (参考 clan_info.py) ---
def get_resource_path(filename):
    """获取资源文件的绝对路径"""
    resource_path = PIC_SRC_DIR / filename
    if not resource_path.exists():
        print(f"警告: 资源文件不存在 - {resource_path}")
        # 如果找不到文件，可以返回一个默认图片路径
        return f"file://{PIC_SRC_DIR}/default.png"
    return f"file://{resource_path.absolute()}"

# --- 图片转 Base64 编码函数 ---
def _image_to_base64(image_path: Path) -> str | None:
    """将图片文件读取并转换为 Base64 data URI 格式"""
    if not image_path.is_file():
        print(f"警告: 图片文件不存在 - {image_path}")
        return None
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # 根据文件扩展名确定 MIME 类型
        mime_type = "image/png"  # 默认使用 PNG
        if image_path.suffix.lower() == '.jpg' or image_path.suffix.lower() == '.jpeg':
            mime_type = "image/jpeg"
        elif image_path.suffix.lower() == '.gif':
            mime_type = "image/gif"
        elif image_path.suffix.lower() == '.svg':
            mime_type = "image/svg+xml"
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"编码图片 {image_path} 时出错: {e}")
        return None

# 预先加载并编码图片
BONUS_RAID_BASE64 = _image_to_base64(BONUS_RAID_IMG_PATH)
NOBONUS_RAID_BASE64 = _image_to_base64(NOBONUS_RAID_IMG_PATH)
CAPITAL_RESOURCE_BASE64 = _image_to_base64(CAPITAL_RESOURCE_IMG_PATH)

# --- HTML 模板 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>部落突袭详情</title>
    <style>
        body {{
            font-family: 'HarmonyOS Sans SC', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
        }}
        #container {{
            background-color: #fff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
            width: 95%;
            max-width: 800px;
            box-sizing: border-box;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.7em;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        #member-list {{
            display: grid;
            grid-template-columns: repeat(5, 1fr); /* 固定5列 */
            gap: 15px;
            margin-top: 15px;
        }}
        .member-card {{
            background-color: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }}
        /* 进攻状态样式 */
        .full-attacks {{ 
            background-color: rgba(200, 250, 200, 0.4); /* 浅绿色 - 打满 */
            border-color: rgba(76, 175, 80, 0.5);
        }}
        .partial-attacks {{ 
            background-color: rgba(255, 243, 200, 0.4); /* 浅黄色 - 打了但没打满 */
            border-color: rgba(255, 193, 7, 0.5);
        }}
        .zero-attacks {{ 
            background-color: rgba(255, 200, 200, 0.4); /* 浅红色 - 没打 */
            border-color: rgba(239, 83, 80, 0.5);
        }}
        
        .member-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
        }}
        .rank-badge {{
            position: absolute;
            top: 0px;
            left: 0px;
            background-color: #3498db;
            color: white;
            padding: 3px 8px;
            font-size: 0.8em;
            font-weight: bold;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            line-height: 1;
        }}
        .rank-badge.top1 {{ background-color: #e74c3c; }}
        .rank-badge.top2 {{ background-color: #f39c12; }}
        .rank-badge.top3 {{ background-color: #f1c40f; }}

        .member-name {{
            font-weight: bold;
            color: #333;
            margin-top: 15px;
            margin-bottom: 8px;
            font-size: 0.85em;
            text-align: center;
            word-break: break-all;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 2px;
        }}
        .member-stats {{
            margin-top: 0;
            font-size: 0.85em;
            color: #555;
            text-align: center;
        }}
        .member-stats-row {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px; /* 减小两列之间的间距 */
            margin: 4px 0;
        }}
        .stat-item {{
            display: flex;
            align-items: center;
            white-space: nowrap;
        }}
        .stat-icon {{
            width: 14px; /* 减小图标尺寸 */
            height: 14px;
            margin-left: 4px;
            vertical-align: middle;
        }}
        .zero-attack {{
            opacity: 0.8;
        }}
         .zero-attack:hover {{
            transform: none;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>突袭详情</h1>
        <div id="member-list">
            {member_cards}
        </div>
    </div>
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="member-card {card_class}">
    <span class="rank-badge {rank_class}">{rank}</span>
    <div class="member-name">{name}</div>
    <div class="member-stats">
        <div class="member-stats-row">
            <div class="stat-item">
                <span>{attacks}/{max_attacks}</span>
                <img src="{attack_icon_b64}" alt="攻击" class="stat-icon">
            </div>
            <div class="stat-item">
                <span>{loot}</span>
                <img src="{capital_resource_b64}" alt="紫币" class="stat-icon">
            </div>
        </div>
    </div>
</div>
"""

# --- 数据处理函数 ---
def process_raid_data(data):
    """处理 JSON 数据，合并成员和突袭信息，并排序，包含已离开但在突袭中进攻的成员"""
    current_members_list = data.get('members', [])
    raids = data.get('raids', [])
    raid_members_list = raids[0].get('members', []) if raids else []

    # 使用字典合并数据，以 tag 为 key
    all_members_data = {}

    # 创建突袭成员详细信息字典以便快速查找 (包含战利品)
    raid_member_details = {
        m['tag']: {
            'attacks': m.get('attacks', 0),
            'attackLimit': m.get('attackLimit', 5), # Default limit 5
            'bonusAttackLimit': m.get('bonusAttackLimit', 1), # Default bonus 1
            'capitalResourcesLooted': m.get('capitalResourcesLooted', 0) # Include loot
        } for m in raid_members_list
    }

    # 1. 处理当前部落成员
    for member in current_members_list:
        tag = member['tag']
        details = raid_member_details.get(tag)
        loot = 0
        attacks = 0
        max_attacks = 5 + 1 # Default max attacks

        if details:
            # 成员参与了突袭，从 details 获取数据
            attacks = details['attacks']
            max_attacks = details['attackLimit'] + details['bonusAttackLimit']
            loot = details['capitalResourcesLooted'] # Correctly get loot from details
        # else:
            # 成员未参与突袭，使用默认值 (attacks=0, loot=0, max_attacks=default)

        all_members_data[tag] = {
            'name': member['name'],
            'tag': tag,
            'clanRank': member.get('clanRank', 999),
            'attacks': attacks,
            'max_attacks': max_attacks,
            'capitalResourcesLooted': loot, # Assign loot correctly
            'is_current_member': True
        }

    # 2. 处理仅在突袭记录中出现的（已离开）成员
    for raid_member in raid_members_list:
        tag = raid_member['tag']
        if tag not in all_members_data:
            # 添加已离开但在本次突袭有数据的成员
            name = raid_member.get('name', f"已离开成员({tag[-4:]})")
            attacks = raid_member.get('attacks', 0)
            attack_limit = raid_member.get('attackLimit', 5)
            bonus_attack_limit = raid_member.get('bonusAttackLimit', 1)
            max_attacks = attack_limit + bonus_attack_limit
            loot = raid_member.get('capitalResourcesLooted', 0)

            all_members_data[tag] = {
                'name': name,
                'tag': tag,
                'clanRank': 1000,
                'attacks': attacks,
                'max_attacks': max_attacks,
                'capitalResourcesLooted': loot,
                'is_current_member': False
            }

    # 转换字典为列表
    processed_members = list(all_members_data.values())

    # # 确保所有成员都有 capitalResourcesLooted 键 (No longer needed with corrected logic)
    # for member_data in processed_members:
    #     if 'capitalResourcesLooted' not in member_data:
    #         member_data['capitalResourcesLooted'] = 0


    # 分离进攻者和未进攻者 (现在基于战利品或进攻次数)
    attackers = [m for m in processed_members if m.get('attacks', 0) > 0 or m.get('capitalResourcesLooted', 0) > 0]
    non_attackers = [m for m in processed_members if m.get('attacks', 0) == 0 and m.get('capitalResourcesLooted', 0) == 0]

    # 排序
    # 进攻者按战利品降序
    attackers.sort(key=lambda x: x.get('capitalResourcesLooted', 0), reverse=True)
    # 未进攻者按部落排名升序
    non_attackers.sort(key=lambda x: x.get('clanRank', 1000))

    # 合并排序后的列表
    sorted_members = attackers + non_attackers

    return sorted_members, data.get('name', '未知部落')

# --- 获取未完成突袭进攻的成员标签 ---
def get_incomplete_raid_attackers_tags(data):
    """
    从JSON数据中获取未完成突袭进攻的成员标签列表
    
    参数:
        data: JSON数据（字典格式），包含部落及突袭信息
        
    返回:
        未完成突袭进攻的成员标签列表，格式为 ['#标签1', '#标签2', ...]
        如果处理失败，返回空列表
    """
    try:
        # 获取数据
        current_members_list = data.get('members', [])
        raids = data.get('raids', [])
        
        # 检查数据有效性
        if not current_members_list:
            print("警告: 未找到成员列表数据")
            return []
            
        if not raids:
            print("警告: 未找到突袭数据")
            return []
            
        raid_members_list = raids[0].get('members', [])
        if not raid_members_list:
            print("警告: 突袭成员列表为空")

        # 创建突袭成员字典以便快速查找 {tag: {'attacks': count, 'limit': limit, 'bonus': bonus}}
        raid_member_details = {
            m['tag']: {
                'attacks': m.get('attacks', 0),
                'attackLimit': m.get('attackLimit', 5), # Default limit 5
                'bonusAttackLimit': m.get('bonusAttackLimit', 1) # Default bonus 1
            } for m in raid_members_list
        }

        incomplete_attackers_tags = []

        for current_member in current_members_list:
            tag = current_member['tag']
            details = raid_member_details.get(tag)

            if details:
                attacks = details['attacks']
                max_attacks = details['attackLimit'] + details['bonusAttackLimit']
            else:
                # 当前成员未参与突袭记录 (但也算未完成)
                attacks = 0
                max_attacks = 5 + 1 # Assume default limits

            # 检查成员进攻次数是否小于其最大进攻次数
            if attacks < max_attacks:
                incomplete_attackers_tags.append(tag)

        return incomplete_attackers_tags
        
    except Exception as e:
        print(f"获取未完成突袭进攻成员时出错: {e}")
        return []

# --- HTML 生成函数 ---
def generate_clan_raids_html(members):
    """根据成员数据生成 HTML 卡片"""
    member_cards = ""
    rank = 1
    
    # 检查 Base64 图像数据是否成功加载
    bonus_raid_img = BONUS_RAID_BASE64 or "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3C/svg%3E"
    nobonus_raid_img = NOBONUS_RAID_BASE64 or "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3C/svg%3E"
    capital_resource_img = CAPITAL_RESOURCE_BASE64 or "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3C/svg%3E"

    for member in members:
        attacks = member.get('attacks', 0)
        max_attacks = member.get('max_attacks', 6)
        loot = member.get('capitalResourcesLooted', 0)
        
        # 根据进攻完成情况确定卡片样式类
        if attacks == 0:
            card_class = "zero-attacks" # 没有进攻 - 浅红色
        elif attacks == max_attacks:
            card_class = "full-attacks" # 打满 - 浅绿色
        else:
            card_class = "partial-attacks" # 打了但没打满 - 浅黄色
            
        # 添加原来的 zero-attack 类，用于降低未进攻成员的显示优先级
        if attacks == 0 and loot == 0:
            card_class += " zero-attack"

        rank_class = ""
        if rank == 1: rank_class = "top1"
        elif rank == 2: rank_class = "top2"
        elif rank == 3: rank_class = "top3"

        # 根据 max_attacks 选择正确的图标
        attack_icon_b64 = bonus_raid_img if max_attacks == 6 else nobonus_raid_img

        member_cards += CARD_TEMPLATE.format(
            rank=rank,
            name=member['name'],
            attacks=attacks,
            max_attacks=max_attacks,
            loot=f"{loot}",
            card_class=card_class,
            rank_class=rank_class,
            attack_icon_b64=attack_icon_b64,
            capital_resource_b64=capital_resource_img
        )
        rank += 1
    return HTML_TEMPLATE.format(member_cards=member_cards)

# --- Playwright 截图函数 ---
def generate_clan_raids_image(json_data, output_path):
    """
    直接从JSON数据生成部落突袭详情图片
    
    参数:
        json_data: JSON数据（字典格式），包含部落及突袭信息
        output_path: 输出图片路径
    
    返回:
        成功时返回输出路径，失败时返回None
    """
    try:
        # 1. 处理数据
        sorted_members, _ = process_raid_data(json_data)
        if not sorted_members:
            print("未能处理成员数据。")
            return None
            
        # 2. 生成 HTML
        html_content = generate_clan_raids_html(sorted_members)
        
        # 3. 使用 Playwright 截图
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            # 减小视口宽度，适合手机观看
            page.set_viewport_size({"width": 850, "height": 1000})
            page.set_content(html_content)

            # 定位到包含内容的容器
            container = page.locator('#container')
            if not container.is_visible():
                print("错误：无法找到 #container 元素或元素不可见。")
                browser.close()
                return None

            # 动态调整高度以适应内容
            bounding_box = container.bounding_box()
            if bounding_box:
                # 增加一点额外的padding
                new_height = bounding_box['height'] + 50
                # 检查高度是否合理，防止过大或过小
                new_height = max(600, min(new_height, 8000)) # 设置最小和最大高度
                page.set_viewport_size({"width": 850, "height": int(new_height)}) # 保持宽度一致

            # 截取特定元素的截图
            container.screenshot(path=output_path)
            browser.close()
            return output_path
            
    except Exception as e:
        print(f"生成突袭详情图片时出错: {e}")
        return None

# --- 主函数 ---
def main():
    # 1. 读取 JSON 文件
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: JSON 文件未找到于 '{JSON_FILE_PATH}'")
        return
    except json.JSONDecodeError:
        print(f"错误: 无法解析 JSON 文件 '{JSON_FILE_PATH}'")
        return
    except Exception as e:
        print(f"读取或解析 JSON 文件时发生错误: {e}")
        return

    # 2. 直接调用图片生成函数
    generate_clan_raids_image(data, OUTPUT_IMAGE_PATH)

if __name__ == "__main__":
    # 确保 Playwright 浏览器已安装
    # 可以运行 `playwright install chromium` 来安装
    print("正在生成部落突袭详情图片...")
    main()
    
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        incomplete_tags = get_incomplete_raid_attackers_tags(test_data)
        print("\n未完成突袭进攻的成员标签:")
        print(incomplete_tags)
    except Exception as e:
        print(f"测试新函数时出错: {e}") 