from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime, timedelta
import ssl
import logging
import base64
from io import BytesIO

# 创建不验证SSL的context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 定义脚本路径和项目根目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# 定义图标路径 - 使用绝对路径
PIC_SRC_DIR = PROJECT_ROOT / "storage" / "pic_src"

# 定义英雄和装备的对应关系（从player_info.py中复制）
hero_equipment_map = {
    'Barbarian King': ['Barbarian Puppet', 'Rage Vial', 'Earthquake Boots', 'Vampstache', 'Giant Gauntlet', 'Spiky Ball', 'Snake Bracelet'],
    'Archer Queen': ['Archer Puppet', 'Invisibility Vial', 'Giant Arrow', 'Healer Puppet', 'Frozen Arrow', 'Magic Mirror', 'Action Figure'],
    'Minion Prince': ['Dark Orb', 'Henchmen Puppet', 'Metal Pants', 'Noble Iron'],
    'Grand Warden': ['Eternal Tome', 'Life Gem', 'Rage Gem', 'Healing Tome', 'Fireball', 'Lavaloon Puppet'],
    'Royal Champion': ['Royal Gem', 'Seeking Shield', 'Haste Vial', 'Hog Rider Puppet', 'Rocket Spear', 'Electro Boots']
}

# 英雄列表（从player_info.py中复制）
hero_order = ['Barbarian King', 'Archer Queen', 'Minion Prince', 'Grand Warden', 'Royal Champion']

def image_to_base64_data_uri(image_path):
    """读取图片文件并返回Base64编码的Data URI"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            # 根据文件扩展名确定MIME类型，这里假定都是png
            mime_type = "image/png"
            return f"data:{mime_type};base64,{encoded_string}"
    except FileNotFoundError:
        print(f"错误：图片文件未找到: {image_path}")
        # 返回一个小的透明像素的Data URI作为占位符
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    except Exception as e:
        print(f"错误：读取或编码图片时出错 {image_path}: {e}")
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

def get_date_range(days=1):
    """获取最近几天的日期列表，从当前日期往前推"""
    today = datetime.now()
    date_list = []
    for i in range(days):
        day = today - timedelta(days=i)
        date_list.append(day.strftime("%Y-%m-%d"))
    return date_list

def timestamp_to_time(ts):
    """将时间戳转换为时间（小时:分钟:秒）"""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%H:%M:%S")

def get_most_recent_day_data(data):
    """获取最近一天的传奇联赛数据（有进攻或防守数据的最后一天）"""
    # 按日期倒序排列所有天数
    legend_days = sorted(data.get('legends', {}).keys(), reverse=True)
    
    if not legend_days:
        return None, None
    
    # 找到有进攻或防守数据的最后一天
    for day in legend_days:
        day_data = data['legends'][day]
        has_attacks = len(day_data.get('new_attacks', [])) > 0
        has_defenses = len(day_data.get('new_defenses', [])) > 0
        
        if has_attacks or has_defenses:
            return day, day_data
    
    # 如果所有天都没有进攻或防守数据，返回最新的一天
    latest_day = legend_days[0]
    return latest_day, data['legends'][latest_day]

def get_final_trophies(day_data):
    """
    通过new_attacks和new_defenses中time值最大的元素所包含的trophies属性来确定当天最终奖杯
    如果都没有，则返回None
    """
    max_time = 0
    final_trophies = None
    
    # 检查进攻记录
    for attack in day_data.get('new_attacks', []):
        if attack.get('time', 0) > max_time and 'trophies' in attack:
            max_time = attack['time']
            final_trophies = attack['trophies']
    
    # 检查防守记录
    for defense in day_data.get('new_defenses', []):
        if defense.get('time', 0) > max_time and 'trophies' in defense:
            max_time = defense['time']
            final_trophies = defense['trophies']
    
    return final_trophies

def get_last_attack_equipment(attacks):
    """获取最后一场进攻的英雄装备信息"""
    if not attacks:
        return None
    
    # 按时间排序获取最后一场进攻
    sorted_attacks = sorted(attacks, key=lambda x: x.get('time', 0))
    if not sorted_attacks:
        return None
    
    # 获取最后一场进攻的装备
    last_attack = sorted_attacks[-1]
    return last_attack.get('hero_gear', [])

def generate_player_legend_html(data):
    """生成玩家冲杯信息的HTML"""
    # 获取玩家基本信息
    player_name = data.get('name', 'Unknown')
    player_tag = data.get('tag', '#UNKNOWN')
    
    # 获取排名信息
    rankings = data.get('rankings', {})
    global_rank = rankings.get('global_rank', 'N/A')
    country_name = rankings.get('country_name', 'Unknown')
    country_code = rankings.get('country_code', 'XX')
    
    # 获取最近一天的传奇联赛数据
    today, day_data = get_most_recent_day_data(data)
    
    if not day_data:
        return f"""<!DOCTYPE html>
<html><body><h1>没有找到传奇联赛数据</h1></body></html>"""
    
    # 获取当日最终奖杯数
    current_trophies = get_final_trophies(day_data)
    if current_trophies is None:
        current_trophies = 5000  # 默认值
    
    # 准备进攻记录和防守记录，按时间排序
    attacks = day_data.get('new_attacks', [])
    defenses = day_data.get('new_defenses', [])
    
    # 按时间排序
    attacks = sorted(attacks, key=lambda x: x.get('time', 0))
    defenses = sorted(defenses, key=lambda x: x.get('time', 0))
    
    # 获取最后一场进攻的装备
    last_attack_gear = get_last_attack_equipment(attacks)
    
    # 生成装备HTML
    equipment_html = ""
    if last_attack_gear:
        # 按英雄组织装备
        hero_equipment_items = {}
        
        for item in last_attack_gear:
            name = item.get('name')
            level = item.get('level', 0)
            
            # 找到对应的英雄
            for hero, equipments in hero_equipment_map.items():
                if name in equipments:
                    if hero not in hero_equipment_items:
                        hero_equipment_items[hero] = []
                    
                    hero_equipment_items[hero].append({
                        'name': name,
                        'level': level,
                        'max_level': 27 if name in ['Spiky Ball', 'Electro Boots'] else 18  # 根据已知信息设置最大等级
                    })
                    break
        
        # 将英雄分成两行显示（每行最多3个）
        hero_rows = []
        current_row = []
        
        for hero in hero_order:
            if hero in hero_equipment_items and hero_equipment_items[hero]:
                current_row.append((hero, hero_equipment_items[hero]))
                if len(current_row) == 3:  # 每行3个英雄
                    hero_rows.append(current_row)
                    current_row = []
        
        # 处理最后一行（可能不满3个英雄）
        if current_row:
            hero_rows.append(current_row)
        
        # 为每行生成HTML
        for row in hero_rows:
            row_html = '<div class="hero-row">'
            
            for hero, equipments in row:
                # 英雄图标路径
                hero_icon_file_path = (PIC_SRC_DIR / f'heroes/{hero}.png').absolute()
                hero_icon_data_uri = image_to_base64_data_uri(hero_icon_file_path)
                
                # 装备HTML
                hero_equipment_html = ""
                for equip in equipments:
                    eq_name = equip['name']
                    eq_level = equip['level']
                    eq_max_level = equip['max_level']
                    
                    # 装备图标路径
                    eq_icon_file_path = (PIC_SRC_DIR / f'equipments/{eq_name}.png').absolute()
                    eq_icon_data_uri = image_to_base64_data_uri(eq_icon_file_path)

                    
                    # 设置装备类型样式
                    equipment_class = "equipment-item"
                    
                    hero_equipment_html += f"""
                    <div class="{equipment_class.strip()}">
                        <img class="equipment-icon" src="{eq_icon_data_uri}">
                        <div class="equipment-level">{eq_level}</div>
                    </div>
                    """
                
                row_html += f"""
                <div class="hero-item">
                    <div class="hero-icon">
                        <img src="{hero_icon_data_uri}" style="width:100%;height:100%;object-fit:contain;">
                    </div>
                    <div class="hero-divider"></div>
                    <div class="equipment-grid">
                        {hero_equipment_html}
                    </div>
                </div>
                """
            
            row_html += '</div>'
            equipment_html += row_html
    
    # 准备图表数据 - 所有传奇联赛数据
    chart_dates = []
    trophies_progression = []
    
    # 获取所有日期，按时间顺序排序
    sorted_dates = sorted(data.get('legends', {}).keys())
    
    for date in sorted_dates:
        chart_dates.append(date)
        daily_data = data['legends'][date]
        
        # 获取当天最终奖杯
        final_trophy = get_final_trophies(daily_data)
        if final_trophy is not None:
            trophies_progression.append(final_trophy)
    
    # 获取奖杯图标的 Data URI
    trophy_icon_path = (PIC_SRC_DIR / "clan" / "clan_points.png").absolute()
    trophy_icon_data_uri = image_to_base64_data_uri(trophy_icon_path)
    
    # 计算净上分
    total_attack_change = sum(attack.get('change', 0) for attack in attacks)
    total_defense_change = sum(defense.get('change', 0) for defense in defenses)
    # 确保防守奖杯变化为负数
    if total_defense_change > 0:
        total_defense_change = -total_defense_change
    net_change = total_attack_change + total_defense_change
    
    # 设置净上分的CSS类
    net_change_class = "positive-result" if net_change >= 0 else "negative-result"
    net_change_symbol = "+" if net_change > 0 else ""
    
    # 创建HTML模板
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: "HarmonyOS Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 0;
            color: #333;
        }}
        .container {{
            width: 750px; /* 手机屏幕宽度 */
            margin: 0 auto;
            background-color: white;
            border-radius: 0; /* 移除圆角 */
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .header {{
            padding: 25px;
            background-color: white;
            color: #333;
            display: flex;
            justify-content: space-between;
            gap: 25px;
        }}
        .header-left {{
            flex: 2;
            display: flex;
            flex-direction: column;
            background: linear-gradient(to bottom, #f7f9fc, #fff);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .player-info {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom:.5px;
        }}
        .player-name {{
            font-size: 36px;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
            text-shadow: 0 1px 1px rgba(0,0,0,0.1);
        }}
        .player-tag {{
            font-size: 16px;
            color: #666;
            background-color: #f0f2f5;
            padding: 3px 10px;
            border-radius: 20px;
        }}
        .header-chart {{
            flex: 1;
            min-height: 140px;
            padding: 10px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) inset;
        }}
        .header-chart-title {{
            font-size: 16px;
            font-weight: 500;
            color: #3498db;
            margin-bottom: 8px;
            text-align: center;
            position: relative;
        }}
        .header-chart-title:after {{
            content: '';
            display: block;
            width: 40px;
            height: 2px;
            background-color: #3498db;
            position: absolute;
            bottom: -4px;
            left: 50%;
            transform: translateX(-50%);
            border-radius: 2px;
        }}
        .header-right {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #f9f9f9;
            border-radius: 10px;
            padding: 0;
            overflow: hidden;
        }}
        .stats-info {{
            display: flex;
            flex-direction: column;
            height: 100%;
            gap: 0;
        }}
        .stat-item {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: white;
            padding: 20px 10px;
            border-radius: 0;
            box-shadow: none;
            flex: 1;
            position: relative;
            transition: all 0.2s ease;
            border-bottom: 1px solid #f0f0f0;
        }}
        .stat-item:last-child {{
            border-bottom: none;
        }}
        .stat-item:hover {{
            background-color: #f7f9fc;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            opacity: 0.8;
        }}
        .trophy-icon {{
            width: 36px;
            height: 36px;
            margin-right: 8px;
        }}
        .date-header {{
            font-size: 18px;
            color: #3498db;
            text-align: center;
            margin-bottom: 15px;
        }}
        .section {{
            margin: 15px;
            padding: 20px;
            background: #fff;
            border-radius: 15px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border: 1px solid #f0f0f0;
        }}
        .section-title {{
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #1e5799;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .battle-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .battle-table th, .battle-table td {{
            padding: 12px 15px;
            text-align: center;
            border-bottom: 1px solid #e9ecef;
        }}
        .battle-table th {{
            background-color: #f1f8ff;
            color: #2980b9;
            font-weight: bold;
            font-size: 16px;
        }}
        .battle-table tbody tr:hover {{
            background-color: #f1f8ff;
        }}
        .battle-table tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .positive-result {{
            color: #27ae60;
            font-weight: bold;
            font-size: 16px;
        }}
        .negative-result {{
            color: #e74c3c;
            font-weight: bold;
            font-size: 16px;
        }}
        .country-flag {{
            width: 24px;
            height: 16px;
            margin-right: 6px;
            vertical-align: middle;
        }}
        /* 英雄装备相关的样式 */
        .hero-section {{
            margin-top: 15px;
        }}
        .hero-row {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            justify-content: flex-start;
        }}
        .hero-item {{
            flex: 0 0 calc(33.33% - 7px); /* 固定宽度，不再使用flex:1 */
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid #e9ecef;
            box-sizing: border-box; /* 确保padding不会增加元素宽度 */
        }}
        .hero-icon {{
            width: 50px;  /* 缩小尺寸 */
            height: 50px; /* 缩小尺寸 */
            position: relative;
            border-radius: 8px;
            background-color: rgba(32, 96, 128, 0.05);
            overflow: hidden;
            border: 1px solid #ddd; /* 添加边框 */
        }}
        .hero-divider {{
            width: 1px;
            height: 100%;
            background: repeating-linear-gradient(
                to bottom,
                #e9ecef,
                #e9ecef 2px,
                transparent 2px,
                transparent 4px
            );
            margin: 0 5px;
        }}
        .equipment-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
            gap: 8px;
            padding: 5px;
            flex: 1;
        }}
        .equipment-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0;
            border-radius: 8px;
            position: relative;
            width: 40px;
            height: 40px;
            margin: 0;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            background-color: rgba(52, 152, 219, 0.05);
            border: 1px solid rgba(52, 152, 219, 0.2);
        }}
        .equipment-icon {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        .equipment-level {{
            position: absolute;
            bottom: 0;
            left: 0;
            color: #fff;
            padding: 1px 3px;
            font-size: 10px;
            font-weight: bold;
            border-radius: 0 4px 0 0;
            background-color: rgba(0, 0, 0, 0.7);
        }}
        /* 两栏式布局 */
        .battles-container {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-top: 15px;
        }}
        .battles-column {{
            flex: 1;
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            overflow: hidden;
        }}
        .column-title {{
            font-size: 16px;
            font-weight: bold;
            padding: 12px;
            text-align: center;
            background-color: #f7f9fc;
            color: #1e5799;
            border-bottom: 1px solid #eee;
        }}
        .battle-table {{
            width: 100%;
            border-collapse: collapse;
            border-radius: 8px;
            overflow: hidden;
        }}
        .battle-table td {{
            padding: 10px;
            text-align: center;
            border-bottom: 1px solid #f5f5f5;
        }}
        .battle-table tbody tr:hover {{
            background-color: #f9f9f9;
        }}
        .battle-table tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .positive-result {{
            color: #27ae60;
            font-weight: bold;
            font-size: 16px;
        }}
        .negative-result {{
            color: #e74c3c;
            font-weight: bold;
            font-size: 16px;
        }}
        /* 净上分样式 */
        .net-change-container {{
            display: flex;
            align-items: center;
            font-size: 16px;
        }}
        .net-change-label {{
            font-weight: bold;
            color: #666;
            margin-right: 8px;
        }}
        .net-change-value {{
            font-weight: bold;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <div class="player-info">
                    <div class="player-name">{player_name}</div>
                    <div class="player-tag">{player_tag}</div>
                </div>
                <div class="header-chart-title">奖杯曲线</div>
                <div class="header-chart">
                    <canvas id="trophiesChart"></canvas>
                </div>
            </div>
            
            <div class="header-right">
                <div class="stats-info">
                    <div class="stat-item">
                        <div class="stat-value">
                            <img src="{trophy_icon_data_uri}" class="trophy-icon" alt="Trophy" style="filter: drop-shadow(0 2px 3px rgba(0,0,0,0.15));">
                            {current_trophies}
                        </div>
                        <div class="stat-label">当前奖杯</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">#{global_rank}</div>
                        <div class="stat-label">全球排名</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">
                            <img src="https://flagcdn.com/w20/{country_code.lower()}.png" style="width: 20px; height: 14px; margin-right: 5px;" alt="{country_name}" />
                            {country_name}
                        </div>
                        <div class="stat-label">国家</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">
                战斗记录
                <div class="net-change-container">
                    <div class="net-change-label">净上分:</div>
                    <div class="net-change-value {net_change_class}">{net_change_symbol}{net_change}</div>
                </div>
            </h2>
            <div class="battles-container">
                <div class="battles-column">
                    <div class="column-title">进攻</div>
"""
    
    # 生成进攻记录
    sorted_attacks = sorted(attacks, key=lambda x: x.get('time', 0))
    
    if sorted_attacks:
        html += """
                    <table class="battle-table">
                        <tbody>
        """
        
        # 添加每个进攻记录
        for attack in sorted_attacks:
            time_stamp = attack.get('time', 0)
            attack_time = timestamp_to_time(time_stamp) if time_stamp else "未知时间"
            trophy_change = attack.get('change', 0)
            
            change_class = "positive-result" if trophy_change >= 0 else "negative-result"
            change_symbol = "+" if trophy_change > 0 else ""
            
            html += f"""
                            <tr>
                                <td>{attack_time}</td>
                                <td class="{change_class}">{change_symbol}{trophy_change}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
        """
    else:
        html += """
                    <div style="padding: 20px; text-align: center; color: #6c757d;">
                        暂无进攻记录
                    </div>
        """
    
    html += """
                </div>
                <div class="battles-column">
                    <div class="column-title">防守</div>
    """
    
    # 生成防守记录
    sorted_defenses = sorted(defenses, key=lambda x: x.get('time', 0))
    
    if sorted_defenses:
        html += """
                    <table class="battle-table">
                        <tbody>
        """
        
        # 添加每个防守记录
        for defense in sorted_defenses:
            time_stamp = defense.get('time', 0)
            defense_time = timestamp_to_time(time_stamp) if time_stamp else "未知时间"
            trophy_change = defense.get('change', 0)
            
            # 确保防守奖杯显示为负数
            if trophy_change > 0:
                trophy_change = -trophy_change
            
            change_class = "negative-result"
            
            html += f"""
                            <tr>
                                <td class="{change_class}">{trophy_change}</td>
                                <td>{defense_time}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
        """
    else:
        html += """
                    <div style="padding: 20px; text-align: center; color: #6c757d;">
                        暂无防守记录
                    </div>
        """
    
    html += f"""
                </div>
            </div>
        </div>
    """
    
    # 添加最后一场进攻的装备显示
    if equipment_html:
        html += f"""
        <div class="section">
            <h2 class="section-title">使用装备</h2>
            <div class="hero-section">
                {equipment_html}
            </div>
        </div>
        """
    
    # 结束HTML
    html += f"""
    </div>
    
    <script>
        // 绘制奖杯曲线图
        const ctx = document.getElementById('trophiesChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 150);
        gradient.addColorStop(0, 'rgba(52, 152, 219, 0.2)');
        gradient.addColorStop(1, 'rgba(52, 152, 219, 0.0)');
        
        const trophiesChart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_dates)},
                datasets: [{{
                    label: '奖杯',
                    data: {json.dumps(trophies_progression)},
                    fill: true,
                    backgroundColor: gradient,
                    borderColor: '#3498db',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    tension: 0.3,
                    borderCapStyle: 'round',
                    cubicInterpolationMode: 'monotone'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                animation: {{
                    duration: 2000,
                    easing: 'easeOutQuart'
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        titleFont: {{
                            size: 14
                        }},
                        bodyFont: {{
                            size: 14
                        }},
                        padding: 10,
                        displayColors: false,
                        callbacks: {{
                            title: function() {{ return ''; }},
                            label: function(context) {{
                                return `奖杯: ${{context.raw}}`;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        min: 5000,
                        grid: {{
                            color: 'rgba(0, 0, 0, 0.05)',
                            borderColor: 'rgba(0, 0, 0, 0.1)',
                            drawBorder: false
                        }},
                        ticks: {{
                            color: '#666',
                            font: {{
                                size: 10
                            }},
                            maxTicksLimit: 3,
                            padding: 10
                        }}
                    }},
                    x: {{
                        display: false,
                        grid: {{
                            display: false
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html

def generate_player_legend_image(data, output_path=None):
    """
    生成玩家冲杯信息图片
    
    Args:
        data: 包含玩家信息的数据字典
        output_path: 图片保存路径
    
    Returns:
        图片保存路径
    """
    logger = logging.getLogger('PlayerLeagueImage')
    
    try:
        # 生成HTML内容
        html_content = generate_player_legend_html(data)
        
        # 使用Playwright渲染HTML为图片
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 750, "height": 1600})
            
            # 设置HTML内容
            page.set_content(html_content)
            
            # 等待图表渲染完成
            page.wait_for_timeout(1000)
            
            # 获取实际内容高度
            body_height = page.evaluate('document.body.scrollHeight')
            
            # 调整页面大小以适应内容
            page.set_viewport_size({"width": 750, "height": body_height})
            
            # 截图保存
            if output_path:
                page.screenshot(path=output_path, full_page=True)
                logger.info(f"冲杯信息图片已生成: {output_path}")
            else:
                # 生成临时文件名
                timestamp = int(time.time())
                output_path = f"/tmp/player_legend_{timestamp}.png"
                page.screenshot(path=output_path, full_page=True)
                logger.info(f"冲杯信息图片已生成(临时文件): {output_path}")
            
            browser.close()
        
        return output_path
    
    except Exception as e:
        logger.error(f"生成冲杯信息图片失败: {str(e)}")
        raise RuntimeError(f"生成冲杯信息图片失败: {str(e)}")

if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 读取测试数据
    test_file = os.path.join(current_dir, "test.json")
    with open(test_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    # 生成图片
    output = os.path.join(current_dir, "player_legend_test.png")
    generate_player_legend_image(test_data, output)
    print(f"图片已生成: {output}")
