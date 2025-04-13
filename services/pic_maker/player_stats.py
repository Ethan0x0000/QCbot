import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64
from urllib.request import urlopen
from io import BytesIO

# 定义图标路径 - 使用项目相对路径
PIC_SRC_DIR = Path(__file__).parent.parent.parent / "storage/pic_src"

# 修改职位显示
role_map = {
    'coLeader': '副首领',
    'leader': '首领',
    'elder': '长老',
    'member': '成员'
}

# 定义英雄和装备的对应关系
hero_equipment_map = {
    'Barbarian King': ['Barbarian Puppet', 'Rage Vial', 'Earthquake Boots', 'Vampstache', 'Giant Gauntlet', 'Spiky Ball', 'Snake Bracelet'],
    'Archer Queen': ['Archer Puppet', 'Invisibility Vial', 'Giant Arrow', 'Healer Puppet', 'Frozen Arrow', 'Magic Mirror', 'Action Figure'],
    'Minion Prince': ['Dark Orb', 'Henchmen Puppet', 'Metal Pants', 'Noble Iron'],
    'Grand Warden': ['Eternal Tome', 'Life Gem', 'Rage Gem', 'Healing Tome', 'Fireball', 'Lavaloon Puppet'],
    'Royal Champion': ['Royal Gem', 'Seeking Shield', 'Haste Vial', 'Hog Rider Puppet', 'Rocket Spear', 'Electro Boots']
}

# 定义英雄顺序
hero_order = ['Barbarian King', 'Archer Queen', 'Minion Prince', 'Grand Warden', 'Royal Champion']

#定义战宠列表
pet_list = [
    'L.A.S.S.I', 'Mighty Yak', 'Electro Owl', 'Unicorn', 'Frosty', 'Diggy', 'Poison Lizard', 'Phoenix', 'Spirit Fox', 'Angry Jelly', 'Sneezy'
]

# 定义攻城器列表
machine_list = [
    'Wall Wrecker', 'Battle Blimp', 'Stone Slammer', 'Siege Barracks', 'Log Launcher', 'Flame Flinger', 'Battle Drill', 'Troop Launcher'
]

# 定义不需要显示的超级部队列表
excluded_troops = {
    'Super Barbarian', 'Super Archer', 'Sneaky Goblin', 'Super Wall Breaker',
    'Super Giant', 'Rocket Balloon', 'Super Wizard', 'Super Dragon',
    'Inferno Dragon', 'Super Minion', 'Super Valkyrie', 'Super Witch',
    'Ice Hound', 'Super Bowler', 'Super Miner', 'Super Hog Rider'
}

# 计算完成度的函数
def calculate_completion(items):
    if not items:
        return 0
    total = sum(item['level'] for item in items)
    max_total = sum(item['maxLevel'] for item in items)
    return int((total / max_total) * 100) if max_total > 0 else 0

# 创建HTML模板
html_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: "Microsoft YaHei", sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            margin-bottom: 20px;
            gap: 20px;
            padding: 30px;
            background: linear-gradient(135deg, #f8f8f8 0%, #e8e8e8 100%);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            min-height: 200px;
        }}
        .player-info {{
            flex: 2;
            padding: 20px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .player-info-content {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}
        .player-name {{
            font-size: 48px;
            font-weight: bold;
            margin: 0;
            color: #333;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }}
        .player-details {{
            display: flex;
            gap: 30px;
            margin: 15px 0;
            justify-content: center;
        }}
        .player-level, .town-hall-level {{
            color: #555;
            font-size: 24px;
            display: flex;
            align-items: center;
        }}
        .player-level::before, .town-hall-level::before {{
            content: "•";
            margin-right: 8px;
            color: #888;
        }}
        .labels {{
            display: flex;
            gap: 15px;
            margin-top: 15px;
        }}
        .label {{
            width: 60px;
            height: 60px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .label:hover {{
            transform: scale(1.05);
        }}
        .clan-info {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            justify-content: center;
        }}
        .clan-badge {{
            width: 120px;
            height: 120px;
            margin-bottom: 15px;
            border-radius: 50%;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .clan-name {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }}
        .clan-role {{
            font-size: 22px;
            color: #666;
            padding: 10px 20px;
            background-color: #f0f0f0;
            border-radius: 20px;
            margin-top: 15px;
        }}
        .trophy-info {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            justify-content: center;
        }}
        .trophy-icon {{
            width: 120px;
            height: 120px;
            margin-bottom: 20px;
        }}
        .trophy-count {{
            font-size: 40px;
            font-weight: bold;
            color: #333;
        }}
        .best-trophies {{
            margin-top: 20px;
            font-size: 22px;
            color: #666;
        }}
        .section {{
            margin: 25px 0;
            padding: 15px;
            background: linear-gradient(135deg, #f8f8f8 0%, #e8e8e8 100%);
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .section-title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            margin-left: 15px;
            margin-right: 15px;
            color: #333;
            padding-bottom: 12px;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .completion {{
            font-size: 0.8em;
            color: #888;
            font-weight: normal;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
            gap: 15px;
            padding: 15px;
        }}
        .grid-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
            width: 72px;
            height: 72px;
            position: relative;
        }}
        .item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 10px;
            background-color: #fff;
            border-radius: 8px;
            position: relative;
            width: 72px;
            height: 72px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        .item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .item.max-level {{
            border: 2px solid gold;
            box-shadow: 0 0 10px rgba(255,215,0,0.3);
        }}
        .hero {{
            background-color: rgba(32, 96, 128, 0.1);
        }}
        .equipment {{
            background-color: rgba(204, 153, 51, 0.1);
        }}
        .spell {{
            background-color: rgba(204, 51, 153, 0.1);
        }}
        .troop {{
            background-color: rgba(51, 204, 102, 0.1);
        }}
        .hero-section {{
            display: flex;
            flex-direction: column;
        }}
        .hero-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            background-color: transparent;
            box-shadow: none;
            border-radius: 8px;
        }}
        .hero-icon {{
            width: 80px;
            height: 80px;
            position: relative;
            border-radius: 8px;
            background-color: rgba(32, 96, 128, 0.1);
        }}
        .hero-level {{
            position: absolute;
            bottom: 0;
            left: 0;
            color: #fff;
            padding: 2px 6px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 3px;
            background-color: rgba(0, 0, 0, 0.8);
        }}
        .hero-divider {{
            width: 1px;
            height: 100%;
            background: repeating-linear-gradient(
                to bottom,
                #ccc,
                #ccc 2px,
                transparent 2px,
                transparent 4px
            );
            margin: 0 5px;
        }}
        .equipment-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
            gap: 15px;
            padding: 10px;
            flex: 1;
        }}
        .equipment-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0;
            border-radius: 8px;
            position: relative;
            width: 72px;
            height: 72px;
            margin: 0;
        }}
        .equipment-item.common {{
            background-color: rgba(100, 200, 255, 0.3); /* 浅蓝色背景 */
        }}

        .equipment-item.epic {{
            background-color: rgba(150, 100, 255, 0.3); /* 紫色背景 */
        }}

        .equipment-icon {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 8px;
        }}
        .equipment-level {{
            position: absolute;
            bottom: 0;
            left: 0;
            color: #fff;
            padding: 2px 6px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 3px;
            background-color: rgba(0, 0, 0, 0.8);
        }}
        .equipment-item.locked {{
            opacity: 0.7;
            border: 1px dashed #ccc;
        }}
        .equipment-item.locked .equipment-level {{
            background-color: rgba(0,0,0,0.8);
        }}
        .unit-section {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .unit-item {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 15px;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }}
        .unit-icon {{
            width: 72px;
            height: 72px;
            position: relative;
            border-radius: 8px;
        }}
        .unit-icon.hero {{
            background-color: rgba(32, 96, 128, 0.1);
        }}
        .unit-icon.spell {{
            background-color: rgba(204, 51, 153, 0.1);
        }}
        .unit-icon.troop {{
            background-color: rgba(51, 204, 102, 0.1);
        }}
        .unit-level {{
            position: absolute;
            bottom: 0;
            left: 0;
            color: #fff;
            padding: 2px 6px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            background-color: rgba(0, 0, 0, 0.8);
        }}
        .max-level {{
            border: 2px solid gold;
            box-shadow: 0 0 10px rgba(255,215,0,0.3);
        }}
        .max-level .hero-level,
        .max-level .equipment-level,
        .max-level .unit-level {{
            color: gold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="trophy-info">
                <img class="trophy-icon" src="{trophy_icon}" alt="Trophy">
                <div class="trophy-count">{trophies}</div>
                <div class="best-trophies">历史最高: {best_trophies}</div>
            </div>
            <div class="player-info">
                <div class="player-info-content">
                    <h1 class="player-name">{name}</h1>
                    <div class="player-details">
                        <div class="player-level">等级: {exp_level}</div>
                        <div class="town-hall-level">大本营等级: {town_hall_level}</div>
                    </div>
                    <div class="labels">
                        {labels_html}
                    </div>
                </div>
            </div>
            <div class="clan-info">
                <img class="clan-badge" src="{clan_badge}" alt="Clan Badge">
                <div class="clan-name">{clan_name}</div>
                <div class="clan-role">{clan_role}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                <span>英雄</span>
                <span class="completion">
                    {heroes_completion}% | 
                    {equipments_completion}%
                </span>
            </h2>
            <div class="hero-section">
                {heroes_html}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                <span>战宠</span>
                <span class="completion">
                    {pets_completion}%
                </span>
            </h2>
            <div class="grid">
                {pets_html}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                <span>部队</span>
                <span class="completion">
                    {troops_completion}%
                </span>
            </h2>
            <div class="grid">
                {troops_html}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                <span>法术</span>
                <span class="completion">
                    {spells_completion}%
                </span>
            </h2>
            <div class="grid">
                {spells_html}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">
                <span>攻城器</span>
                <span class="completion">
                    {machines_completion}%
                </span>
            </h2>
            <div class="grid">
                {machines_html}
            </div>
        </div>
    </div>
</body>
</html>'''


def generate_player_stats(data):
    """
    生成玩家统计HTML页面
    
    Args:
        data: 玩家数据字典
        
    Returns:
        生成的HTML内容
    """
    # 提取关键数据
    name = data['name']
    labels = data['labels']
    exp_level = data['expLevel']
    town_hall_level = data['townHallLevel']
    clan = data['clan']
    trophies = data['trophies']
    heroes = data['heroes']
    hero_equipment = data['heroEquipment']
    spells = data['spells']
    troops = data['troops']
    
    # 生成标签HTML
    labels_html = ""
    for label in labels:
        response = urlopen(label['iconUrls']['small'])
        img_data = response.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        labels_html += f'<img class="label" src="data:image/png;base64,{img_base64}" alt="Label">'

    # 获取部落徽章
    response = urlopen(clan['badgeUrls']['small'])
    clan_badge_data = response.read()
    clan_badge = f"data:image/png;base64,{base64.b64encode(clan_badge_data).decode('utf-8')}"

    # 获取奖杯图标
    response = urlopen(data['league']['iconUrls']['small'])
    trophy_icon_data = response.read()
    trophy_icon = f"data:image/png;base64,{base64.b64encode(trophy_icon_data).decode('utf-8')}"

    # 生成英雄HTML
    heroes_html = ""
    for hero_name in hero_order:
        # 查找匹配的英雄
        matched_hero = None
        for hero in heroes:
            if hero['name'] == hero_name and hero['village'] == 'home':
                matched_hero = hero
                break
        
        if matched_hero:
            level_text = str(matched_hero['level'])
            max_level_class = "max-level" if matched_hero['level'] == matched_hero['maxLevel'] else ""
            hero_icon_path = PIC_SRC_DIR / f"heroes/{hero_name}.png"

            # 生成装备HTML
            equipment_html = ""
            # 获取该英雄对应的装备列表
            hero_equipment_list = hero_equipment_map.get(hero_name, [])
            
            # 按照指定顺序生成装备HTML
            for eq_name in hero_equipment_list:
                # 查找匹配的装备
                matched_equipment = None
                for equipment in hero_equipment:
                    if equipment.get('name') == eq_name:
                        matched_equipment = equipment
                        break
                
                eq_icon_path = PIC_SRC_DIR / f"equipments/{eq_name}.png"
                if matched_equipment:
                    eq_level_text = str(matched_equipment['level'])
                    eq_max_level_class = "max-level" if matched_equipment['level'] == matched_equipment['maxLevel'] else ""
                    if matched_equipment['maxLevel'] == 18:
                        equipment_class = "equipment-item common"
                    elif matched_equipment['maxLevel'] == 27:
                        equipment_class = "equipment-item epic"
                    equipment_html += f"""
                    <div class="{equipment_class} {eq_max_level_class}">
                        <img class="equipment-icon" src="{eq_icon_path}">
                        <div class="equipment-level">{eq_level_text}</div>
                    </div>
                    """
                else:
                    # 未解锁的装备
                    equipment_html += f"""
                    <div class="equipment-item locked">
                        <img class="equipment-icon gray" src="{eq_icon_path}">
                        <div class="equipment-level">?</div>
                    </div>
                    """
            
            heroes_html += f"""
            <div class="hero-item">
                <div class="hero-icon {max_level_class}">
                    <img src="{hero_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="hero-level">{level_text}</div>
                </div>
                <div class="hero-divider"></div>
                <div class="equipment-grid">
                    {equipment_html}
                </div>
            </div>
            """

    # 生成战宠HTML
    pets_html = ""
    for troop in troops:
        if troop['village'] == 'home' and troop['name'] in pet_list:
            level_text = str(troop['level'])
            max_level_class = "max-level" if troop['level'] == troop['maxLevel'] else ""
            pet_icon_path = PIC_SRC_DIR / f"pets/{troop['name']}.png"
            pets_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon troop">
                    <img src="{pet_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """

    # 生成法术HTML
    spells_html = ""
    for spell in spells:
        if spell['village'] == 'home':  # 只处理home村的法术
            level_text = str(spell['level'])
            max_level_class = "max-level" if spell['level'] == spell['maxLevel'] else ""
            spell_icon_path = PIC_SRC_DIR / f"spells/{spell['name']}.png"
            spells_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon spell">
                    <img src="{spell_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """

    # 生成部队HTML
    troops_html = ""
    for troop in troops:
        if (troop['village'] == 'home' and 
            troop['name'] not in excluded_troops and
            troop['name'] not in pet_list and
            troop['name'] not in machine_list):
            level_text = str(troop['level'])
            max_level_class = "max-level" if troop['level'] == troop['maxLevel'] else ""
            troop_icon_path = PIC_SRC_DIR / f"troops/{troop['name']}.png"
            troops_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon troop">
                    <img src="{troop_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """

    machines_html = ""
    for troop in troops:
        if troop['village'] == 'home' and troop['name'] in machine_list:
            level_text = str(troop['level'])
            max_level_class = "max-level" if troop['level'] == troop['maxLevel'] else ""
            machine_icon_path = PIC_SRC_DIR / f"machines/{troop['name']}.png"
            machines_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon troop">
                    <img src="{machine_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """

    # 移除部落名称的编码处理，因为JSON已经正确编码
    clan_name = clan['name']

    # 提取历史最高奖杯数和部落职位
    best_trophies = data['bestTrophies']
    clan_role = role_map.get(data['role'], data['role'])

    # 计算完成度
    heroes_completion = calculate_completion([h for h in heroes if h['village'] == 'home'])
    equipments_completion = calculate_completion([e for e in hero_equipment if e['village'] == 'home'])
    pets_completion = calculate_completion([t for t in troops if t['village'] == 'home' and t['name'] in pet_list])
    troops_completion = calculate_completion([t for t in troops if t['village'] == 'home' and t['name'] not in excluded_troops and t['name'] not in pet_list and t['name'] not in machine_list])
    spells_completion = calculate_completion([s for s in spells if s['village'] == 'home'])
    machines_completion = calculate_completion([t for t in troops if t['village'] == 'home' and t['name'] in machine_list])

    # 创建格式化字典（确保包含所有需要的键）
    format_dict = {
        'name': name,
        'exp_level': exp_level,
        'town_hall_level': town_hall_level,
        'labels_html': labels_html,
        'clan_badge': clan_badge,
        'clan_name': clan_name,
        'clan_role': clan_role,
        'trophy_icon': trophy_icon,
        'trophies': trophies,
        'best_trophies': best_trophies,
        'heroes_html': heroes_html,
        'spells_html': spells_html,
        'troops_html': troops_html,
        'pets_html': pets_html,
        'machines_html': machines_html,
        'heroes_completion': heroes_completion,
        'equipments_completion' : equipments_completion,
        'pets_completion': pets_completion,
        'troops_completion': troops_completion,
        'spells_completion': spells_completion,
        'machines_completion': machines_completion
    }

    # 填充HTML模板
    html_content = html_template.format_map(format_dict)
    return html_content

def generate_player_stats_image(data, output_path=None):
    """
    生成玩家统计图片
    
    Args:
        data: 玩家数据字典
        output_path: 输出图片路径，如果为None则使用默认路径
        
    Returns:
        生成的图片路径
    """
    # 生成HTML内容
    html_content = generate_player_stats(data)
    
    # 创建临时HTML文件
    temp_html_path = Path('temp.html')
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 如果未指定输出路径，使用默认路径
    if output_path is None:
        output_path = 'player_stats.png'
    
    # 使用Playwright截图
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'file://{temp_html_path.absolute()}')
        page.screenshot(path=output_path, full_page=True)
        browser.close()
    
    # 删除临时HTML文件
    temp_html_path.unlink()
    
    return output_path
