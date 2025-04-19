from pathlib import Path
from playwright.sync_api import sync_playwright
import base64
import ssl
from urllib.request import urlopen
from io import BytesIO

# 创建不验证SSL的context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 定义图标路径 - 使用项目相对路径
PIC_SRC_DIR = Path(__file__).parent.parent.parent / "storage/pic_src"

# 职位对应列表
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

# 定义英雄列表
hero_order = ['Barbarian King', 'Archer Queen', 'Minion Prince', 'Grand Warden', 'Royal Champion']

#定义战宠列表
pet_list = [
    'L.A.S.S.I', 'Mighty Yak', 'Electro Owl', 'Unicorn', 'Frosty', 'Diggy', 'Poison Lizard', 'Phoenix', 'Spirit Fox', 'Angry Jelly', 'Sneezy'
]

# 定义部队列表
troop_list = [
    # 圣水兵种
    'Barbarian', 'Archer', 'Giant', 'Goblin', 'Wall Breaker', 'Balloon', 'Wizard', 'Healer', 'Dragon', 'P.E.K.K.A',
    'Baby Dragon', 'Miner','Electro Dragon', 'Yeti', 'Dragon Rider', 'Electro Titan', 'Root Rider', 'Thrower',
    # 暗黑兵种
    'Minion', 'Hog Rider', 'Valkyrie', 'Golem', 'Witch', 'Lava Hound', 'Bowler', 'Ice Golem', 'Headhunter',
    'Apprentice Warden', 'Druid', 'Furnace',
]

# 定义法术列表
spell_list = [
    # 圣水法术
    'Lightning Spell', 'Healing Spell', 'Rage Spell', 'Jump Spell', 'Freeze Spell', 'Clone Spell',
    'Invisibility Spell', 'Recall Spell', 'Revive Spell',
    # 暗黑法术
    'Poison Spell', 'Earthquake Spell', 'Haste Spell', 'Skeleton Spell', 'Bat Spell', 'Overgrowth Spell',
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
            font-family: "HarmonyOS Sans SC", sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 0;
            width: 1360px;
        }}
        .container {{
            width: 1360px;
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
            flex: 3;
            padding: 20px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        .player-info-content {{
            display: flex;
            flex-direction: row;
            align-items: center;
            text-align: center;
            justify-content: center;
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            gap: 10px;
        }}
        .player-info-right {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding-left: 5px;
            flex: 1;
        }}
        .player-name-level {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
            justify-content: center;
        }}
        .player-info-bottom {{
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }}
        .player-name {{
            font-size: 48px;
            font-weight: bold;
            margin: 0;
            color: #333;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
        .player-level {{
            color: #555;
            font-size: 24px;
            display: flex;
            align-items: center;
            position: relative;
        }}
        .player-level {{
            width: 64px;
            height: 64px;
        }}
        .town-hall-level {{
            width: 160px;
            height: 160px;
        }}
        .exp-icon {{
            width: 64px;
            height: 64px;
            position: relative;
            border-radius: 8px;
            overflow: hidden;
        }}
        .th-icon {{
            width: 160px;
            height: 160px;
            position: relative;
            border-radius: 8px;
            overflow: hidden;
        }}
        .exp-level {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
            font-size: 22px;
            color: #fff;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
        }}
        .labels {{
            display: flex;
            gap: 10px;
        }}
        .label {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .player-tag {{
            font-size: 32px;
            color: #777;
            margin: 0;
            text-align: left;
            display: inline-block;
            vertical-align: middle;
            margin-right: 15px;
        }}
        .clan-info {{
            flex: 0.8;
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
            width: 100px;
            height: 100px;
            margin-bottom: 10px;
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
            flex: 0.8;
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
            width: 100px;
            height: 100px;
            margin-bottom: 15px;
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
            justify-content: center;
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
            grid-template-columns: repeat(7, 72px);
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
            background-color: rgba(59, 139, 204, 0.5); /* 浅蓝色背景 */
        }}

        .equipment-item.epic {{
            background-color: rgba(143, 64, 158, 0.5); /* 紫色背景 */
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
            background-color: rgba(100, 100, 100, 0.8); /* Grey background for level */
        }}
        .equipment-item.locked img {{ /* Apply filter to the image inside locked equipment */
            filter: grayscale(100%);
            opacity: 0.6;
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
            border-radius: 3px;
            background-color: rgba(0, 0, 0, 0.8);
        }}
        .max-level {{
            border: 3px solid gold; /* Increased border width */
            box-shadow: 0 0 12px rgba(255, 215, 0, 0.5); /* Enhanced shadow */
        }}
        .max-level .hero-level,
        .max-level .equipment-level,
        .max-level .unit-level {{
            color: #000;
            background-color: gold;
        }}
        /* Style for missing/locked items */
        .locked-item img {{
            filter: grayscale(100%);
            opacity: 0.6;
        }}
        .locked-item .unit-level,
        .locked-item .hero-level {{
             background-color: rgba(100, 100, 100, 0.8); /* Grey background for level */
             color: #ccc; /* Lighter text for locked level */
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
                    <div class="town-hall-level">
                        <div class="th-icon">
                            <img src="{town_hall_icon}" style="width:100%;height:100%;object-fit:contain;">
                        </div>
                    </div>
                    <div class="player-info-right">
                        <div class="player-name-level">
                            <div class="player-level">
                                <div class="exp-icon">
                                    <img src="{exp_icon}" style="width:100%;height:100%;object-fit:contain;">
                                    <div class="exp-level">{exp_level}</div>
                                </div>
                            </div>
                            <h1 class="player-name">{name}</h1>
                        </div>
                        <div class="player-info-bottom">
                            <div class="player-tag">{tag}</div>
                            <div class="labels">
                                {labels_html}
                            </div>
                        </div>
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
                <span class="completion">完成度：
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
                <span class="completion">完成度：
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
                <span class="completion">完成度：
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
                <span class="completion">完成度：
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
                <span class="completion">完成度：
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


def generate_player_info(data):
    """
    生成玩家统计HTML页面
    
    Args:
        data: 玩家数据字典
        
    Returns:
        生成的HTML内容
    """
    # 提取关键数据
    name = data['name']
    tag = data.get('tag', '')  # 获取玩家标签
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
        response = urlopen(label['iconUrls']['small'], context=ssl_context)
        img_data = response.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        labels_html += f'<img class="label" src="data:image/png;base64,{img_base64}" alt="Label">'

    # 获取部落徽章
    if 'clan' in data:
        response = urlopen(clan['badgeUrls']['small'], context=ssl_context)
        clan_badge_data = response.read()
        clan_badge = f"data:image/png;base64,{base64.b64encode(clan_badge_data).decode('utf-8')}"
    else:
        clan_badge = PIC_SRC_DIR / "default/noClan.png"

    # 获取奖杯图标
    if 'league' in data:
        response = urlopen(data['league']['iconUrls']['small'], context=ssl_context)
        trophy_icon_data = response.read()
        trophy_icon = f"data:image/png;base64,{base64.b64encode(trophy_icon_data).decode('utf-8')}"
    else:
        trophy_icon = PIC_SRC_DIR / "default/noLeague.png"
        
    # 获取经验等级和大本营图标
    exp_icon = PIC_SRC_DIR / "member/exp.png"
    town_hall_icon = PIC_SRC_DIR / f"member/{town_hall_level}.png"

    # 生成英雄HTML
    heroes_html = ""
    player_heroes_map = {hero['name']: hero for hero in heroes if hero['village'] == 'home'}

    for hero_name in hero_order:
        # 查找匹配的英雄
        matched_hero = player_heroes_map.get(hero_name)
        hero_icon_path = PIC_SRC_DIR / f"heroes/{hero_name}.png"

        if matched_hero:
            level_text = str(matched_hero['level'])
            max_level_class = "max-level" if matched_hero['level'] == matched_hero['maxLevel'] else ""
            # 生成装备HTML
            equipment_html = ""
            hero_equipment_list = hero_equipment_map.get(hero_name, [])
            player_equipment_map = {eq.get('name'): eq for eq in hero_equipment if eq.get('village') == 'home'}

            for eq_name in hero_equipment_list:
                matched_equipment = player_equipment_map.get(eq_name)
                eq_icon_path = PIC_SRC_DIR / f"equipments/{eq_name}.png"

                if matched_equipment:
                    eq_level_text = str(matched_equipment['level'])
                    eq_max_level_class = "max-level" if matched_equipment['level'] == matched_equipment['maxLevel'] else ""
                    equipment_class = "equipment-item "
                    if matched_equipment['maxLevel'] == 18:
                        equipment_class += "common"
                    elif matched_equipment['maxLevel'] == 27:
                        equipment_class += "epic"
                    
                    equipment_html += f"""
                    <div class="{equipment_class.strip()} {eq_max_level_class}">
                        <img class="equipment-icon" src="{eq_icon_path}">
                        <div class="equipment-level">{eq_level_text}</div>
                    </div>
                    """
                else:
                    # 未解锁的装备
                    equipment_html += f"""
                    <div class="equipment-item locked">
                        <img class="equipment-icon" src="{eq_icon_path}">
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
        else:
             # 未解锁的英雄
            equipment_html = "" # Ensure equipment_html is defined even for locked heroes
            hero_equipment_list = hero_equipment_map.get(hero_name, [])
            for eq_name in hero_equipment_list:
                 eq_icon_path = PIC_SRC_DIR / f"equipments/{eq_name}.png"
                 equipment_html += f"""
                 <div class="equipment-item locked">
                    <img class="equipment-icon" src="{eq_icon_path}">
                    <div class="equipment-level">?</div>
                 </div>
                 """

            heroes_html += f"""
            <div class="hero-item locked-item">
                <div class="hero-icon">
                    <img src="{hero_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="hero-level">?</div>
                </div>
                <div class="hero-divider"></div>
                <div class="equipment-grid">
                    {equipment_html}
                </div>
            </div>
            """

    # 生成战宠HTML
    pets_html = ""
    # 优化：先将玩家部队数据转换为字典以便快速查找
    player_troops_map = {troop['name']: troop for troop in troops if troop['village'] == 'home'}

    for pet_name in pet_list:
        troop = player_troops_map.get(pet_name)
        pet_icon_path = PIC_SRC_DIR / f"pets/{pet_name}.png"
        if troop:
            level_text = str(troop['level'])
            max_level_class = "max-level" if troop['level'] == troop['maxLevel'] else ""
            pets_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon troop">
                    <img src="{pet_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """
        else:
             # 未解锁的战宠
            pets_html += f"""
            <div class="grid-item locked-item">
                 <div class="unit-icon troop">
                     <img src="{pet_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                     <div class="unit-level">?</div>
                 </div>
            </div>
            """

    # 生成法术HTML
    spells_html = ""
    # 优化：先将玩家法术数据转换为字典以便快速查找
    player_spells_map = {spell['name']: spell for spell in spells if spell['village'] == 'home'}

    for spell_name in spell_list:
        spell = player_spells_map.get(spell_name)
        spell_icon_path = PIC_SRC_DIR / f"spells/{spell_name}.png"
        if spell:
            level_text = str(spell['level'])
            max_level_class = "max-level" if spell['level'] == spell['maxLevel'] else ""
            spells_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon spell">
                    <img src="{spell_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """
        else:
            # 未解锁的法术
             spells_html += f"""
             <div class="grid-item locked-item">
                 <div class="unit-icon spell">
                     <img src="{spell_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                     <div class="unit-level">?</div>
                 </div>
             </div>
             """

    # 生成部队HTML
    troops_html = ""
    # 优化：player_troops_map 已在战宠部分创建

    for troop_name in troop_list:
        # 跳过超级兵种和战宠，因为它们不在 `troop_list` 中，或单独处理
        # 但为了保险起见，保留检查
        if troop_name in excluded_troops or troop_name in pet_list or troop_name in machine_list:
             continue

        troop = player_troops_map.get(troop_name)
        troop_icon_path = PIC_SRC_DIR / f"troops/{troop_name}.png"
        if troop:
            level_text = str(troop['level'])
            max_level_class = "max-level" if troop['level'] == troop['maxLevel'] else ""
            troops_html += f"""
            <div class="grid-item {max_level_class}">
                <div class="unit-icon troop">
                    <img src="{troop_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                    <div class="unit-level">{level_text}</div>
                </div>
            </div>
            """
        else:
             # 未解锁的部队
             troops_html += f"""
             <div class="grid-item locked-item">
                 <div class="unit-icon troop">
                     <img src="{troop_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                     <div class="unit-level">?</div>
                 </div>
             </div>
             """

    # 生成攻城机器HTML
    machines_html = ""
    # 优化：player_troops_map 已在战宠部分创建

    for machine_name in machine_list:
         troop = player_troops_map.get(machine_name)
         machine_icon_path = PIC_SRC_DIR / f"machines/{machine_name}.png"
         if troop:
             level_text = str(troop['level'])
             max_level_class = "max-level" if troop['level'] == troop['maxLevel'] else ""
             machines_html += f"""
             <div class="grid-item {max_level_class}">
                 <div class="unit-icon troop">
                     <img src="{machine_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                     <div class="unit-level">{level_text}</div>
                 </div>
             </div>
             """
         else:
             # 未解锁的攻城机器
             machines_html += f"""
             <div class="grid-item locked-item">
                 <div class="unit-icon troop">
                     <img src="{machine_icon_path}" style="width:100%;height:100%;object-fit:contain;">
                     <div class="unit-level">?</div>
                 </div>
             </div>
             """

    # 判断部落名是否存在
    clan_name = clan.get('name', '无部落') if clan else '无部落' # More robust check for clan presence

    # 提取历史最高奖杯数和部落职位
    best_trophies = data.get('bestTrophies', 'N/A') # Use get for safer access
    role = data.get('role')
    clan_role = role_map.get(role, role) if role else 'N/A' # Handle missing role

    # 计算完成度 - 需要考虑只计算玩家拥有的项目
    # Convert lists to maps for easier lookup by name
    player_heroes_map = {h['name']: h for h in heroes if h.get('village') == 'home'}
    player_equipment_map = {e.get('name'): e for e in hero_equipment if e.get('village') == 'home'}
    player_troops_map = {t['name']: t for t in troops if t.get('village') == 'home'}
    player_spells_map = {s['name']: s for s in spells if s.get('village') == 'home'}

    # Calculate completion based on items the player has
    heroes_completion = calculate_completion(list(player_heroes_map.values()))
    
    # Filter player equipment based on hero equipment map
    relevant_player_equipment = []
    for hero_name, equipment_list in hero_equipment_map.items():
        for eq_name in equipment_list:
            if eq_name in player_equipment_map:
                relevant_player_equipment.append(player_equipment_map[eq_name])
    equipments_completion = calculate_completion(relevant_player_equipment)

    pets_completion = calculate_completion([player_troops_map[p] for p in pet_list if p in player_troops_map])
    troops_completion = calculate_completion([player_troops_map[t] for t in troop_list if t in player_troops_map and t not in excluded_troops and t not in pet_list and t not in machine_list])
    spells_completion = calculate_completion([player_spells_map[s] for s in spell_list if s in player_spells_map])
    machines_completion = calculate_completion([player_troops_map[m] for m in machine_list if m in player_troops_map])

    # 创建格式化字典（确保包含所有需要的键）
    format_dict = {
        'name': name,
        'tag': tag,  # 添加标签到格式化字典
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
        'machines_completion': machines_completion,
        'exp_icon': exp_icon,
        'town_hall_icon': town_hall_icon
    }

    # 填充HTML模板
    html_content = html_template.format_map(format_dict)
    return html_content

def generate_player_info_image(data, output_path=None):
    """
    生成玩家统计图片
    
    Args:
        data: 玩家数据字典
        output_path: 输出图片路径，如果为None则使用默认路径
        
    Returns:
        生成的图片路径
    """
    # 生成HTML内容
    html_content = generate_player_info(data)
    
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
        page = browser.new_page(viewport={"width": 1360, "height": 1080})
        page.goto(f'file://{temp_html_path.absolute()}')
        page.screenshot(path=output_path, full_page=True)
        browser.close()
    
    # 删除临时HTML文件
    temp_html_path.unlink()
    
    return output_path

if __name__ == "__main__":
    # 测试代码
    import os
    import json

    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 读取测试数据
    test_file = os.path.join(current_dir, "test.json")
    with open(test_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    # 生成图片
    output = os.path.join(current_dir, "player_info_test.png")
    generate_player_info_image(test_data, output)
    print(f"图片已生成: {output}")