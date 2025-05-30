import json
import os
import asyncio
import base64 # 导入 base64 模块
from pathlib import Path
from playwright.sync_api import sync_playwright
from collections import defaultdict # 导入 defaultdict

# 定义图标路径 - 存储文件路径本身
PIC_SRC_DIR = Path(__file__).parent.parent.parent / "storage/pic_src"
WIN_STAR_IMG_PATH = PIC_SRC_DIR / 'member/winstar.png'
LOSE_STAR_IMG_PATH = PIC_SRC_DIR / 'member/losestar.png'

# --- 新增：图片转 Base64 辅助函数 ---
def _image_to_base64(image_path: Path) -> str | None:
    """Reads an image file and returns a Base64 data URI string."""
    if not image_path.is_file():
        print(f"Warning: Image file not found at {image_path}")
        return None
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # 推断 MIME 类型，这里简化处理为 png
        mime_type = "image/png"
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None
# --- 结束新增 ---

# 修改: 函数签名，接收 json_data 而不是 json_path
def generate_player_warhits_image(json_data: dict | list, output_path: str | Path):
    """Processes war data (dict/list), calculates stats, and generates an image using Playwright."""

    # 修改: 移除文件读取逻辑，直接使用 json_data
    # try:
    #     with open(json_path, 'r', encoding='utf-8') as f:
    #         data = json.load(f)
    # except FileNotFoundError:
    #     print(f"Error: JSON file not found at {json_path}")
    #     return
    # except json.JSONDecodeError:
    #     print(f"Error: Could not decode JSON from {json_path}")
    #     return

    # 修改: 直接从 json_data 获取 items
    items = json_data.get('items', []) if isinstance(json_data, dict) else json_data
    if not items or not isinstance(items, list):
        print("Invalid or empty war data provided.")
        return

    # Assuming all items belong to the same player for this analysis
    player_name = items[0].get('member_data', {}).get('name', 'Unknown Player')
    player_tag = items[0].get('member_data', {}).get('tag', 'Unknown Tag')

    # 初始化统计数据结构
    stats = {
        'random': {
            'attacks': {'total': 0, 'stars_total': 0, 'counts': defaultdict(int), 'percentages': {}},
            'defenses': {'total': 0, 'stars_total': 0, 'counts': defaultdict(int), 'percentages': {}},
            'opponent_th_counts': defaultdict(int)
        },
        'cwl': {
            'attacks': {'total': 0, 'stars_total': 0, 'counts': defaultdict(int), 'percentages': {}},
            'defenses': {'total': 0, 'stars_total': 0, 'counts': defaultdict(int), 'percentages': {}},
            'opponent_th_counts': defaultdict(int)
        }
    }

    for item in items:
        war_type = item.get('war_data', {}).get('type') # 'random' or 'cwl'
        if war_type not in stats: # Handle potential unknown war types
            continue

        attacks = item.get('attacks', [])
        defenses = item.get('defenses', [])

        # 统计进攻
        if attacks:
            stats[war_type]['attacks']['total'] += len(attacks)
            for attack in attacks:
                stars = attack.get('stars', 0)
                stats[war_type]['attacks']['stars_total'] += stars
                stats[war_type]['attacks']['counts'][stars] += 1
                defender_th = attack.get('defender', {}).get('townhallLevel')
                if defender_th:
                    stats[war_type]['opponent_th_counts'][defender_th] += 1

        # 统计防守
        if defenses:
            stats[war_type]['defenses']['total'] += len(defenses)
            for defense in defenses:
                stars = defense.get('stars', 0)
                stats[war_type]['defenses']['stars_total'] += stars
                stats[war_type]['defenses']['counts'][stars] += 1

    # 计算平均星数和百分比
    for war_type in stats:
        for category in ['attacks', 'defenses']:
            total_count = stats[war_type][category]['total']
            stars_total = stats[war_type][category]['stars_total']
            stats[war_type][category]['avg_stars'] = (stars_total / total_count) if total_count > 0 else 0

            if total_count > 0:
                for stars in range(4): # 0, 1, 2, 3 stars
                    count = stats[war_type][category]['counts'][stars]
                    stats[war_type][category]['percentages'][stars] = (count / total_count) * 100
            else:
                 for stars in range(4):
                    stats[war_type][category]['percentages'][stars] = 0

    # --- Calculate Overall Score (using existing logic but with new stats structure) ---
    cwl_attack_weight = 6
    random_attack_weight = 4

    cwl_attack_score = (stats['cwl']['attacks']['avg_stars'] / 3 * 100) if stats['cwl']['attacks']['total'] > 0 else 0
    random_attack_score = (stats['random']['attacks']['avg_stars'] / 3 * 100) if stats['random']['attacks']['total'] > 0 else 0
    cwl_defense_score = ((3 - stats['cwl']['defenses']['avg_stars']) / 3 * 100) if stats['cwl']['defenses']['total'] > 0 else 0
    random_defense_score = ((3 - stats['random']['defenses']['avg_stars']) / 3 * 100) if stats['random']['defenses']['total'] > 0 else 0

    total_weighted_score = 0
    total_weight = 0

    if stats['cwl']['attacks']['total'] > 0:
        total_weighted_score += cwl_attack_score * cwl_attack_weight
        total_weight += cwl_attack_weight
    if stats['random']['attacks']['total'] > 0:
        total_weighted_score += random_attack_score * random_attack_weight
        total_weight += random_attack_weight

    final_score = (total_weighted_score / total_weight) if total_weight > 0 else 0
    final_score_str = f"{final_score:.1f}"

    # Helper function to generate star images HTML using Base64
    def _generate_star_images(stars):
        win_stars = stars
        lose_stars = 3 - stars
        img_html = ''
        # 获取 Base64 编码后的图片数据
        win_star_base64 = _image_to_base64(WIN_STAR_IMG_PATH)
        lose_star_base64 = _image_to_base64(LOSE_STAR_IMG_PATH)

        # 仅在成功获取 Base64 数据时添加 img 标签
        if win_star_base64:
            for _ in range(win_stars):
                img_html += f'<img src="{win_star_base64}" alt="Win Star" class="star-image">'
        else:
            img_html += f'<span class="star-placeholder">[Win Star]*{win_stars}</span>' # Fallback text

        if lose_star_base64:
            for _ in range(lose_stars):
                img_html += f'<img src="{lose_star_base64}" alt="Lose Star" class="star-image">'
        else:
            img_html += f'<span class="star-placeholder">[Lose Star]*{lose_stars}</span>' # Fallback text

        return img_html

    # Helper function to generate HTML for star distribution
    def generate_star_details_html(category_stats, sort_descending=False):
        if category_stats['total'] == 0:
            return '<span class="no-data">无数据</span>'

        details_html = '<div class="star-distribution">'
        star_range = range(3, -1, -1) if sort_descending else range(4)
        for stars in star_range:
            count = category_stats['counts'].get(stars, 0)
            percentage = category_stats['percentages'].get(stars, 0)
            star_images_html = _generate_star_images(stars)
            details_html += f'<div class="star-row"><span class="star-label">{star_images_html}</span> <span class="star-count">{count}次</span> <span class="star-percentage">({percentage:.1f}%)</span></div>'
        details_html += '</div>'
        details_html += f'<div class="average-stars">三星率: {category_stats["percentages"].get(3, 0):.1f}%</div>'
        details_html += f'<div class="avg-stars-separate">平均星数: {category_stats["avg_stars"]:.2f}</div>'
        return details_html

    # Helper function to generate opponent TH stats HTML with cards
    def generate_opponent_th_html(th_counts):
        if not th_counts:
            return '<span class="no-data">无进攻数据</span>'
        cards_html = '<div class="th-distribution-cards">'
        for th, count in sorted(th_counts.items()):
            cards_html += f'<div class="th-card">TH{th} <strong>{count}</strong></div>'
        cards_html += '</div>'
        return cards_html

    # --- Generate HTML --- 
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>玩家战争数据</title>
        <style>
            body {{
                font-family: "HarmonyOS Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
                background-color: #f4f7f9; /* Slightly lighter background */
                padding: 25px;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                margin: 0;
            }}
            .container {{
                background: #ffffff;
                padding: 35px 45px; /* Increased padding */
                border-radius: 18px; /* Smoother radius */
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07); /* Softer shadow */
                text-align: center;
                width: 800px; /* Slightly wider */
                border: 1px solid #dde4ea; /* Lighter border */
                margin-top: 25px;
                position: relative;
                box-sizing: border-box;
            }}
            .main-title {{
                 color: #00796b; /* Adjusted main title color */
                 margin-bottom: 15px;
                 font-size: 1.9em;
                 font-weight: 600;
                 letter-spacing: 0.5px;
            }}
            .player-name {{
                color: #263238; /* Darker blue-grey */
                margin-bottom: 8px;
                font-size: 2.1em;
                font-weight: 700;
            }}
            .player-tag {{
                color: #607d8b; /* Softer grey */
                margin-bottom: 30px; /* More space before grid */
                font-size: 1.1em;
                font-weight: 400;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 35px; /* Increased gap */
                margin-top: 25px;
                text-align: left; /* Align content left within columns */
            }}
            .war-type-column {{
                background-color: #fcfdff; /* Very light blue background */
                padding: 25px; /* More padding */
                border-radius: 12px;
                border: 1px solid #e8eef3;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04);
            }}
             /* Differentiate column backgrounds slightly */
            .war-type-column:first-child {{
                 background-color: #f8faff;
            }}
             .war-type-column:last-child {{
                 background-color: #fafff8; /* Light green tint */
            }}
            .war-type-column h4 {{ /* War Type Title (Random/CWL) */
                color: #455a64; /* Slightly muted color */
                margin-top: 0;
                margin-bottom: 25px; /* More space below */
                font-size: 1.5em;
                font-weight: 600;
                border-bottom: 2px solid #dce4ec;
                padding-bottom: 12px;
                text-align: center; /* Center war type titles */
            }}
            .category-section {{
                margin-bottom: 30px; /* More space between Attack/Defense */
            }}
             .category-section:last-child {{
                 margin-bottom: 15px; /* Less margin for the last section */
            }}
            .category-section h5 {{ /* Attack/Defense Title */
                color: #00695c; /* Teal color */
                margin-bottom: 18px;
                font-size: 1.3em;
                font-weight: 600;
                padding-bottom: 5px;
                border-bottom: 1px dashed #b2dfdb; /* Dashed underline */
                display: inline-block; /* Fit border to text */
            }}
            .total-count {{
                font-weight: 500;
                color: #546e7a;
                margin-bottom: 12px;
                font-size: 1.05em; /* Slightly larger */
            }}
            .star-distribution {{
                margin-bottom: 15px; /* More space below distribution */
                padding-left: 5px; /* Less indent needed now */
            }}
            .star-row {{
                margin-bottom: 8px; /* Slightly more space between rows */
                display: flex;
                align-items: center;
                justify-content: space-between; /* Space out elements */
                font-size: 1em; /* Standardize font size */
                padding: 4px 0; /* Add padding for breathing room */
                gap: 20px; /* 增加水平间距 */
            }}
            .star-label {{
                color: #37474f;
                font-weight: 500;
                display: flex; /* Use flex for alignment */
                align-items: center;
                min-width: 75px; /* Adjust as needed */
            }}
            .star-image {{
                height: 1.1em; /* Slightly larger stars */
                vertical-align: middle;
                margin-right: 3px;
                margin-left: 2px; /* Add some left margin for stars */
            }}
             .star-label span {{ /* Text part of label if needed */
                 margin-left: 4px;
             }}
             .star-count {{
                 color: #1e88e5; /* Brighter blue */
                 font-weight: 600; /* Bolder count */
                 text-align: right;
                 min-width: 60px; /* 增加最小宽度 */
             }}
             .star-percentage {{
                 color: #78909c; /* Slightly darker grey */
                 font-size: 0.9em;
                 text-align: right;
                 min-width: 80px; /* 增加最小宽度 */
             }}
            .average-stars, .avg-stars-separate {{
                font-weight: 700; /* Bolder average */
                color: #00897b; /* Stronger teal */
                font-size: 1.1em; /* Slightly larger */
                text-align: left;
            }}
            .average-stars {{
                margin-top: 8px;
                padding: 6px 0;
                border-top: 1px solid #e0e0e0; /* Separator line */
            }}
            .avg-stars-separate {{
                margin-top: 15px; /* 增加间距 */
                padding: 6px 0;
            }}
            .opponent-th-stats {{
                margin-top: 6px; /* 修改: 进一步减少上方间距 */
                padding-top: 8px; /* 修改: 进一步减少上方内边距 */
                border-top: 1px dashed #e8eef3; /* 修改: 更浅的分隔线 */
            }}
            .opponent-th-stats h6 {{
                color: #424242; /* Darker grey */
                margin-bottom: 5px; /* 修改: 进一步减少下方间距 */
                font-size: 1.05em; /* 修改: 略微减小标题 */
                font-weight: 600;
            }}
            .th-level {{
                font-size: 0.95em;
                color: #555;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between; /* Align level and count */
            }}
            .th-level strong {{
                color: #333;
                font-weight: 600; /* Bolder count */
            }}
            .no-data {{
                color: #90a4ae; /* Lighter grey */
                font-style: italic;
                font-size: 1em;
                display: block; /* Ensure it takes block space */
                padding: 10px 0;
            }}
            .overall-score {{
                /* 修改: 恢复绝对定位 */
                position: absolute;
                top: 20px; /* 修改: 调整垂直位置以适应增加的高度 */
                right: 30px; /* 修改: 调整水平位置 */

                /* 修改: 移除块级和居中样式 */
                /* display: block; */
                /* margin: 15px auto 25px auto; */
                /* width: fit-content; */

                /* 修改: 新的徽章/标签样式 */
                background: #e0f2f1; /* 更淡的青色背景 */
                color: #00695c;    /* 文字颜色 */
                padding: 25px 15px; /* 修改: 大幅增加垂直内边距, 调整水平内边距 */
                border-radius: 18px; /* 修改: 调整圆角 */
                font-size: 1.5em;  /* 修改: 增加字体大小 */
                font-weight: 600;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* 更柔和的阴影 */
                text-align: center;
                line-height: 1.2; /* 修改: 调整行高 */
                border: 1px solid #b2dfdb; /* 更淡的边框 */
                /* 强制高度可能不是最佳方式，优先使用 padding */
                /* min-height: 80px; */ 
            }}
            .score-label {{
                font-size: 0.6em;  /* 修改: 调整标签大小 */
                display: block;
                margin-bottom: 5px; /* 修改: 增加标签和数字间距 */
                font-weight: 500;
                color: #00796b; /* 标签颜色 */
                opacity: 1;
                letter-spacing: 0.3px; /* 调整字母间距 */
            }}
            /* Add specific class for CWL column header for potential color overrides */
            .cwl-header {{
                 /* Example: color: #some_cwl_color; */
            }}
             /* Add specific class for Random column header */
             .random-header {{
                 /* Example: color: #some_random_color; */
            }}
             /* Fallback for missing images */
             .star-placeholder {{
                 font-style: italic;
                 color: #b0bec5;
                 font-size: 0.9em;
            }}
            /* 新增: 对手大本营卡片布局样式 */
            .th-distribution-cards {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px; /* 卡片间距 */
                margin-top: 8px; /* 与标题的间距 */
            }}
            .th-card {{
                background-color: #e8f0f3; /* 卡片背景色 */
                padding: 5px 10px; /* 卡片内边距 */
                border-radius: 5px; /* 卡片圆角 */
                font-size: 0.9em; /* 卡片字体大小 */
                color: #37474f; /* 卡片字体颜色 */
                text-align: center;
                border: 1px solid #dce4ec; /* 卡片边框 */
                min-width: 60px; /* 最小宽度 */
                box-sizing: border-box;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05); /* 轻微阴影 */
            }}
            .th-card strong {{
                font-weight: 600;
                color: #1a2a3a; /* 加粗数字颜色 */
                margin-left: 4px; /* 数字与 TH 标签的间距 */
            }}
        </style>
    </head>
    <body>
        <div class="container">
             <!-- 修改: 将 score 移回容器顶部 -->
             <div class="overall-score">
                <span class="score-label">综合评分</span>
                {final_score_str}
            </div>
             <div class="main-title">玩家实力分析</div>
             <div class="player-name">{player_name}</div>
             <div class="player-tag">{player_tag}</div>

             <div class="stats-grid">
                <div class="war-type-column">
                    <h4 class="random-header">部落战</h4>
                    <div class="category-section">
                        <h5>进攻 (总计: {stats['random']['attacks']['total']})</h5>
                        {generate_star_details_html(stats['random']['attacks'], sort_descending=True)}
                        <div class="opponent-th-stats">
                            <h6>对手本位:</h6>
                            {generate_opponent_th_html(stats['random']['opponent_th_counts'])}
                        </div>
                    </div>
                    <div class="category-section">
                        <h5>防守 (总计: {stats['random']['defenses']['total']})</h5>
                        {generate_star_details_html(stats['random']['defenses'], sort_descending=False)}
                    </div>
                </div>

                <div class="war-type-column">
                    <h4 class="cwl-header">联赛</h4>
                    <div class="category-section">
                        <h5>进攻 (总计: {stats['cwl']['attacks']['total']})</h5>
                        {generate_star_details_html(stats['cwl']['attacks'], sort_descending=True)}
                         <div class="opponent-th-stats">
                            <h6>对手本位:</h6>
                            {generate_opponent_th_html(stats['cwl']['opponent_th_counts'])}
                        </div>
                    </div>
                    <div class="category-section">
                        <h5>防守 (总计: {stats['cwl']['defenses']['total']})</h5>
                        {generate_star_details_html(stats['cwl']['defenses'], sort_descending=False)}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # --- Generate Image using Playwright --- 
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        
        # Find the container element and take a screenshot of it
        container_element = page.query_selector('.container')
        if container_element:
            container_element.screenshot(path=output_path)
            print(f"Image successfully generated at {output_path}")
        else:
            print("Error: Could not find the container element to screenshot.")
            # Fallback: screenshot the whole page if container not found
            page.screenshot(path=output_path, full_page=True)
            print(f"Fallback: Screenshotting full page at {output_path}")

        browser.close()

# Example usage (if you want to run this script directly for testing)
def main():
    # Ensure the test JSON path is correct relative to this script's location
    script_dir = os.path.dirname(__file__)
    test_json_path = os.path.join(script_dir, 'test.json') 
    output_image_path = os.path.join(script_dir, 'player_warhits_output.png')

    # 修改: 读取测试 JSON 数据
    test_data = None
    try:
        with open(test_json_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Test JSON file not found at {test_json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode test JSON from {test_json_path}")
        return

    # 修改: 调用函数时传入读取的数据
    if test_data:
        generate_player_warhits_image(test_data, output_image_path)

if __name__ == "__main__":
    main()