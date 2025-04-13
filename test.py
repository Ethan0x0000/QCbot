from services import ClashKing
import json

if __name__ == '__main__':
    ck = ClashKing()
    params = {'tag': "#2QULJC9CU"}
    data = ck.get_data('clan_war', params)
    
    if 'application/json' in data.get('content_type'):
        with open('output.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("数据已保存为output.json")
    elif 'text/html' in data.get('content_type'):
        with open('output.html', 'w', encoding='utf-8') as f:
            f.write(data['content'])
        print("数据已保存为output.html")
    else:
        print(f"未知的content_type: {data.get('content_type')}")
        with open('output.txt', 'w', encoding='utf-8') as f:
            f.write(str(data))
        print("数据已保存为output.txt")
